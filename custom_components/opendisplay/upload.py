from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from io import BytesIO
from typing import Final

import async_timeout
from epaper_dithering import DitherMode
from homeassistant.components.bluetooth import async_ble_device_from_address
from py_atc_ble_oepl import ATCDevice, ATCError
from PIL import Image

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError, HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import DOMAIN, SIGNAL_TAG_IMAGE_UPDATE

_LOGGER: Final = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds


class UploadQueueHandler:
    """Handle queued image uploads to the AP.

    Manages a queue of image upload tasks to prevent overwhelming the AP with concurrent requests.

    Features include:

    - Maximum concurrent upload limit
    - Cooldown period between uploads
    - Task tracking and status reporting

    This helps maintain AP stability while processing multiple image requests from different parts of Home Assistant.
    """

    def __init__(self, max_concurrent: int = 1, cooldown: float = 1.0):
        """Initialize the upload queue handler.

        Args:
            max_concurrent: Maximum number of concurrent uploads (default: 1)
            cooldown: Cooldown period in seconds between uploads (default: 1.0)
        """
        self._queue = asyncio.Queue()
        self._max_concurrent = max_concurrent
        self._cooldown = cooldown
        self._active_uploads = 0
        self._last_upload = None
        self._lock = asyncio.Lock()
        self._processing = False
        self._processor_task = None  # Track the processor task
        self._errors = []  # Collect errors from failed uploads

    def __str__(self):
        """Return queue status string."""
        return f"Queue(active={self._active_uploads}, size={self._queue.qsize()})"

    async def add_to_queue(self, upload_func, *args, **kwargs):
        """Add an upload task to the queue.

        Queues an upload function with its arguments for later execution.
        Starts the queue processor if it's not already running.

        Args:
            upload_func: Async function that performs the actual upload
            *args: Positional arguments to pass to the upload function
            **kwargs: Keyword arguments to pass to the upload function
        """

        entity_id = next((arg for arg in args if isinstance(arg, str) and "." in arg), "unknown")

        _LOGGER.debug("Adding upload task to queue for %s. %s", entity_id, self)
        # Add a task to the queue
        await self._queue.put((upload_func, args, kwargs))

        # Start the processing queue if not already running
        if not self._processing:
            _LOGGER.debug("Starting upload queue processor for %s", entity_id)
            self._processor_task = asyncio.create_task(self._process_queue())

    async def wait_for_current_batch(self):
        """Wait for all currently queued uploads to complete.

        This allows service handlers to wait for uploads without blocking
        the Home Assistant event loop (uses async/await).

        Returns:
            list: List of exception messages from failed uploads (empty if all succeeded)
        """
        if self._processor_task and not self._processor_task.done():
            _LOGGER.debug("Waiting for upload queue to complete")
            await self._processor_task

        # Retrieve any errors that were collected during processing
        if self._errors:
            errors = self._errors.copy()
            self._errors = []  # Clear for next batch
            return errors

        return []  # No errors

    async def _process_queue(self):
        """Process queued upload tasks with true parallelism.

        Long-running task that processes the upload queue, respecting:

        - Maximum concurrent upload limit
        - Cooldown period between uploads

        Creates background tasks for parallel execution instead of blocking.
        Handles errors in individual uploads without stopping queue processing.
        This method runs until the queue is empty, then terminates.
        """
        self._processing = True
        _LOGGER.debug("Upload queue processor started. %s", self)

        running_tasks = set()

        try:
            while not self._queue.empty() or running_tasks:
                # Clean up completed tasks
                if running_tasks:
                    done_tasks = {task for task in running_tasks if task.done()}
                    for task in done_tasks:
                        running_tasks.remove(task)
                        # Get the result to propagate any exceptions
                        try:
                            await task
                        except (ServiceValidationError, HomeAssistantError) as err:
                            # Collect validation and operational errors
                            _LOGGER.error("Background upload task failed: %s", str(err))
                            # Don't raise - collect error and continue processing other uploads
                            if not hasattr(self, '_errors'):
                                self._errors = []
                            self._errors.append(str(err))
                        except Exception as err:
                            # Unexpected errors - collect and continue
                            _LOGGER.error("Unexpected background upload error: %s", str(err), exc_info=True)
                            if not hasattr(self, '_errors'):
                                self._errors = []
                            self._errors.append(f"Unexpected upload error: {str(err)}")

                # Check if new uploads can be started
                async with self._lock:
                    if (not self._queue.empty() and
                            self._active_uploads < self._max_concurrent):

                        # Check cooldown period
                        if self._last_upload:
                            elapsed = (datetime.now() - self._last_upload).total_seconds()
                            if elapsed < self._cooldown:
                                _LOGGER.debug("In cooldown period (%.1f seconds remaining)",
                                              self._cooldown - elapsed)
                                await asyncio.sleep(self._cooldown - elapsed)

                        # Get next task from queue
                        upload_func, args, kwargs = await self._queue.get()
                        entity_id = next((arg for arg in args if isinstance(arg, str) and "." in arg), "unknown")

                        # Create and start background task
                        task = asyncio.create_task(self._execute_upload(upload_func, args, kwargs, entity_id))
                        running_tasks.add(task)

                        # Update last upload timestamp
                        self._last_upload = datetime.now()

                    else:
                        # Wait a bit before checking again
                        await asyncio.sleep(0.1)

        finally:
            self._processing = False
            _LOGGER.debug("Upload queue processor finished. %s", self)
            # Errors are stored in self._errors and will be retrieved by wait_for_current_batch()
            # Don't raise here - let the caller handle them

    async def _execute_upload(self, upload_func, args, kwargs, entity_id):
        """Execute a single upload task in the background."""
        try:
            # TODO don't we need the incrementation logic here?
            _LOGGER.debug("Starting upload for %s", entity_id)
            await upload_func(*args, **kwargs)
            _LOGGER.info("Successfully completed upload for %s", entity_id)

        except (ServiceValidationError, HomeAssistantError) as err:
            # Log and re-raise - let service handler collect errors
            _LOGGER.error("Upload failed for %s: %s", entity_id, str(err))
            raise
        except Exception as err:
            # Unexpected error - wrap and raise
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unexpected_upload",
                translation_placeholders={"entity_id": entity_id, "error": str(err)},
            ) from err
        finally:
            # Decrement active upload counter
            async with self._lock:
                self._active_uploads -= 1
            # Mark task as done
            self._queue.task_done()
            _LOGGER.debug("Upload task for %s finished. %s", entity_id, self)


async def upload_to_atc_ble(hass: HomeAssistant, entity_id: str, img: bytes, dither_mode: DitherMode = DitherMode.ORDERED) -> None:
    """Upload an image to ATC BLE tags using the py-atc-ble-oepl library.

    Replaces the internal block based upload for ATC devices.
    The library handles connection, dithering, compression and image rotation internally.
    """
    mac = entity_id.split(".")[1].upper()
    _LOGGER.debug("Starting ATC BLE upload for %s (MAC: %s)", entity_id, mac)

    try:
        ble_device = async_ble_device_from_address(hass, mac, connectable=True)
        async with ATCDevice(mac, ble_device) as device:
            success = await device.upload_image(
                img,
                dither_mode=dither_mode,
            )
        if not success:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ble_upload_failed",
                translation_placeholders={"entity_id": entity_id}
            )
        async_dispatcher_send(hass, f"{SIGNAL_TAG_IMAGE_UPDATE}_{mac}", img)

    except ATCError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="ble_upload_failed",
            translation_placeholders={"entity_id": entity_id,}
        ) from err
    except HomeAssistantError:
        raise
    except Exception as err:
        _LOGGER.error("Unexpected error during ATC BLE upload for %s: %s", entity_id, str(err), exc_info=True)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="unexpected_ble_upload_error",
            translation_placeholders={"entity_id": entity_id, "error": str(err)},
        ) from err


async def upload_to_opendisplay(
    hass: HomeAssistant,
    entity_id: str,
    img: bytes,
    dither_mode: DitherMode = DitherMode.ORDERED,
    refresh_type: int = 0,
) -> None:
    """Upload image to an OpenDisplay BLE tag using the py-opendisplay library."""
    from opendisplay import OpenDisplayDevice, OpenDisplayError
    from opendisplay.models.enums import RefreshMode

    mac = entity_id.split(".")[1].upper()
    _LOGGER.debug("Starting OpenDisplay BLE upload for %s (MAC: %s)", entity_id, mac)

    encryption_key: bytes | None = None
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.unique_id and entry.unique_id.upper() == mac:
            raw = entry.data.get("encryption_key")
            if raw and len(raw) == 32:
                try:
                    encryption_key = bytes.fromhex(raw)
                except ValueError:
                    pass
            break

    try:
        ble_device = async_ble_device_from_address(hass, mac, connectable=True)
        pil_img = Image.open(BytesIO(img))
        refresh_mode = RefreshMode.FAST if refresh_type == 1 else RefreshMode.FULL

        async with OpenDisplayDevice(
            mac_address=mac, ble_device=ble_device, encryption_key=encryption_key
        ) as device:
            result = await device.upload_image(
                pil_img,
                dither_mode=dither_mode,
                refresh_mode=refresh_mode,
            )

        buf = BytesIO()
        result.convert("RGB").save(buf, format="JPEG", quality=95)
        async_dispatcher_send(hass, f"{SIGNAL_TAG_IMAGE_UPDATE}_{mac}", buf.getvalue())

    except OpenDisplayError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="ble_upload_failed",
            translation_placeholders={"entity_id": entity_id},
        ) from err
    except HomeAssistantError:
        raise
    except Exception as err:
        _LOGGER.error(
            "Unexpected error during OpenDisplay BLE upload for %s: %s", entity_id, str(err), exc_info=True
        )
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="unexpected_ble_upload_error",
            translation_placeholders={"entity_id": entity_id, "error": str(err)},
        ) from err


def create_upload_queues() -> UploadQueueHandler:
    """Create the BLE upload queue."""
    return UploadQueueHandler(max_concurrent=1, cooldown=0.1)