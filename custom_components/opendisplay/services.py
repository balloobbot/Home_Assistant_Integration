from __future__ import annotations

import io
import logging
from datetime import datetime
from functools import wraps
from typing import Final, Any, Callable

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .coordinator import Hub
from .const import DOMAIN, SIGNAL_TAG_IMAGE_UPDATE
from epaper_dithering import DitherMode
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from odl_renderer import generate_image
from .runtime_data import OpenDisplayBLERuntimeData
from .tag_types import get_tag_types_manager
from .upload import create_upload_queues, upload_to_hub, upload_to_atc_ble, upload_to_opendisplay

_LEGACY_DITHER_MAP = {"0": DitherMode.NONE, "1": DitherMode.BURKES, "2": DitherMode.ORDERED}


def _parse_dither_mode(value: str) -> DitherMode:
    if str(value) in _LEGACY_DITHER_MAP:
        return _LEGACY_DITHER_MAP[str(value)]
    return DitherMode[str(value).upper()]
from .util import is_ble_entry, get_hub_from_hass, rgb_to_rgb332, int_to_hex_string, \
    is_ble_device, get_mac_from_entity_id

_LOGGER: Final = logging.getLogger(__name__)


class HADataProvider:
    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get_history(
        self, entity_ids: list[str], start: datetime, end: datetime
    ) -> dict[str, list[dict]]:
        from functools import partial
        from homeassistant.components.recorder import get_instance
        from homeassistant.components.recorder.history import get_significant_states

        raw = await get_instance(self._hass).async_add_executor_job(
            partial(
                get_significant_states,
                self._hass, start, end, entity_ids,
                significant_changes_only=False,
                minimal_response=True,
                no_attributes=False,
            )
        )
        # minimal_response=True: first item per entity is a LazyState object,
        # subsequent items are already {"state", "last_changed"} dicts.
        result = {}
        for entity_id, states in raw.items():
            if not states:
                result[entity_id] = []
                continue
            first = states[0]
            result[entity_id] = [
                {"state": first.state, "last_changed": str(first.last_changed)},
                *states[1:],
            ]
        return result


def _detect_accent_color(color_table: dict) -> str:
    has_red = "red" in color_table
    has_yellow = "yellow" in color_table
    if has_yellow and not has_red:
        return "yellow"
    elif has_red:
        return "red"
    return "black"


async def _get_ap_tag_dimensions(hass: HomeAssistant, entity_id: str) -> tuple[int, int, str]:
    try:
        tag_mac = entity_id.split(".")[1].upper()
    except IndexError:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_entity_id_format",
            translation_placeholders={"entity_id": entity_id},
        )

    hub = get_hub_from_hass(hass)
    if not hub.online:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="ap_offline_core")

    if tag_mac not in hub.tags:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="tag_not_registered",
            translation_placeholders={"tag_mac": tag_mac},
        )
    if tag_mac in hub.get_blacklisted_tags():
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="tag_blacklisted",
            translation_placeholders={"tag_mac": tag_mac},
        )

    tag_data = hub.get_tag_data(tag_mac)
    if not tag_data:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="tag_inconsistent",
            translation_placeholders={"tag_mac": tag_mac},
        )

    hw_type = tag_data.get("hw_type")
    if hw_type is None:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="tag_no_hw_type",
            translation_placeholders={"tag_mac": tag_mac},
        )

    tag_manager = await get_tag_types_manager(hass)
    tag_type = await tag_manager.get_tag_info(hw_type)
    if not tag_type:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="tag_unknown_hw_type",
            translation_placeholders={"hw_type": hw_type},
        )

    try:
        accent_color = _detect_accent_color(getattr(tag_type, "color_table", {}))
    except Exception as e:
        _LOGGER.warning("Error getting accent color, defaulting to red: %s", e)
        accent_color = "red"

    return tag_type.width, tag_type.height, accent_color


async def _get_ble_tag_dimensions(hass: HomeAssistant, entity_id: str) -> tuple[int, int, str]:
    from opendisplay import GlobalConfig
    from epaper_dithering import ColorScheme

    try:
        tag_mac = entity_id.split(".")[1].upper()
    except IndexError:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_entity_id_format",
            translation_placeholders={"entity_id": entity_id},
        )

    runtime_data = None
    for entry in hass.config_entries.async_entries(DOMAIN):
        rd = getattr(entry, "runtime_data", None)
        if isinstance(rd, OpenDisplayBLERuntimeData) and rd.mac_address.upper() == tag_mac:
            runtime_data = rd
            break

    if runtime_data is None:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="ble_no_metadata",
            translation_placeholders={"entity_id": entity_id},
        )

    device_config = runtime_data.device_config
    if isinstance(device_config, GlobalConfig):
        display = device_config.displays[0] if device_config.displays else None
        if not display:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="ble_no_metadata",
                                     translation_placeholders={"entity_id": entity_id})
        width = display.pixel_width
        height = display.pixel_height
        cs = display.color_scheme_enum
        color_scheme = cs if isinstance(cs, ColorScheme) else ColorScheme.from_value(cs)
    else:
        width = device_config.width
        height = device_config.height
        color_scheme = ColorScheme.from_value(device_config.color_scheme)

    return width, height, color_scheme.accent_color


async def _get_tag_dimensions(hass: HomeAssistant, entity_id: str, is_ble: bool) -> tuple[int, int, str]:
    if is_ble:
        return await _get_ble_tag_dimensions(hass, entity_id)
    return await _get_ap_tag_dimensions(hass, entity_id)


async def async_setup_services(hass: HomeAssistant) -> None:
    """
    Set up the OpenDisplay services.
    Args:
        hass: Home Assistant instance
    """

    # Create upload queues
    ble_upload_queue, hub_upload_queue = create_upload_queues()

    async def get_device_ids_from_label_id(label_id: str) -> list[str]:
        """Get device_ids for OpenDisplay devices with a specific label."""
        device_registry = dr.async_get(hass)
        devices = dr.async_entries_for_label(device_registry, label_id)

        open_display_device_ids = []
        for device in devices:
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN:
                    open_display_device_ids.append(device.id)
                    break

        return open_display_device_ids

    async def get_device_ids_from_area_id(area_id: str) -> list[str]:
        """Get device_ids for all OpenDisplay devices in an area."""
        device_registry = dr.async_get(hass)
        devices = dr.async_entries_for_area(device_registry, area_id)
        open_display_device_ids = []
        for device in devices:
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN:
                    open_display_device_ids.append(device.id)
                    break
        return open_display_device_ids

    async def get_entity_id_from_device_id(device_id: str) -> str:
        """Get the primary entity ID for an OpenDisplay device."""
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(device_id)
        if not device:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="device_not_found",
                translation_placeholders={"device_id": device_id},
            )
        if not device.identifiers:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="device_no_identifiers",
                translation_placeholders={"device_id": device_id},
            )

        domain_mac = next(iter(device.identifiers))
        if domain_mac[0] != DOMAIN:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="device_not_opendisplay",
                translation_placeholders={"device_id": device_id},
            )

        identifier = domain_mac[1]
        if identifier.startswith("ble_"):
            mac_address = identifier[4:]
        else:
            mac_address = identifier

        return f"{DOMAIN}.{mac_address.lower()}"


    def _build_led_pattern(service_data: dict[str, Any]) -> str:
        """Build LED pattern hex string from service data."""
        mode = service_data.get("mode", "")
        modebyte = "1" if mode == "flash" else "0"
        brightness = service_data.get("brightness", 2)
        modebyte = hex(((brightness - 1) << 4) + int(modebyte))[2:]

        def _color_segment(color_num: int) -> str:
            default_delay = 0.0 if color_num == 3 else 0.1
            color = service_data.get(f"color{color_num}")
            flash_speed = service_data.get(f"flashSpeed{color_num}", 0.2)
            flash_count = service_data.get(f"flashCount{color_num}", 2)
            delay = service_data.get(f"delay{color_num}", default_delay)

            if not isinstance(color, (list, tuple)) or len(color) != 3:
                color = (0, 0, 0)
                flash_speed = 0
                flash_count = 0

            return (
                    rgb_to_rgb332(color)
                    + hex(int(flash_speed * 10))[2:]
                    + hex(flash_count)[2:]
                    + int_to_hex_string(int(delay * 10))
            )

        return (
                modebyte +
                _color_segment(1) +
                _color_segment(2) +
                _color_segment(3) +
                int_to_hex_string(service_data.get("repeats", 2) - 1) +
                "00"
        )


    def require_hub_online(func: Callable) -> Callable:
        """Decorator to require the AP to be online before executing a service."""
        @wraps(func)
        async def wrapper(service: ServiceCall, *args, **kwargs) -> None:
            hub = get_hub_from_hass(hass)
            if not hub.online:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="ap_offline",
                )
            return await func(service, *args, hub=hub, **kwargs)
        return wrapper

    def handle_targets(func: Callable) -> Callable:
        """Decorator to handle device_id, label_id, and area_id targeting."""
        @wraps(func)
        async def wrapper(service: ServiceCall, *args, **kwargs):
            device_ids = service.data.get("device_id", [])
            label_ids = service.data.get("label_id", [])
            area_ids = service.data.get("area_id", [])

            # Normalize to lists
            if isinstance(device_ids, str):
                device_ids = [device_ids]
            if isinstance(label_ids, str):
                label_ids = [label_ids]
            if isinstance(area_ids, str):
                area_ids = [area_ids]

            # Expand labels
            for label_id in label_ids:
                expanded = await get_device_ids_from_label_id(label_id)
                device_ids.extend(expanded)

            # Expand areas
            for area_id in area_ids:
                expanded = await get_device_ids_from_area_id(area_id)
                device_ids.extend(expanded)

            # Remove duplicates while preserving order
            seen = set()
            unique_device_ids = []
            for device_id in device_ids:
                if device_id not in seen:
                    seen.add(device_id)
                    unique_device_ids.append(device_id)

            if not unique_device_ids:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="no_targets_specified",
                )

            # Process each device
            errors: list[tuple[str, str]] = []
            for device_id in unique_device_ids:
                try:
                    entity_id = await get_entity_id_from_device_id(device_id)
                    await func(service, entity_id, *args, **kwargs)
                except ServiceValidationError as err:
                    errors.append((device_id, str(err)))

                # Wait for all queued uploads to complete
                # This is async/await so it doesn't block the HA event loop
                try:
                    ble_errors = await ble_upload_queue.wait_for_current_batch()
                    hub_errors = await hub_upload_queue.wait_for_current_batch()
                    for ble_error in ble_errors:
                        errors.append((device_id, str(ble_error)))
                    for hub_error in hub_errors:
                        errors.append((device_id, str(hub_error)))
                except (ServiceValidationError, HomeAssistantError) as err:
                    errors.append((device_id, str(err)))

            # If ANY errors occurred across all targets, raise them
            if errors:
                errors_str = "\n".join(f"{entity}: {message}" for entity, message in errors)
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="multiple_errors",
                    translation_placeholders={"errors": errors_str},
                )
        return wrapper

    @handle_targets
    async def drawcustom_service(service: ServiceCall, entity_id: str) -> None:
        """Handle drawcustom service calls.

        Processes requests to generate and upload custom images to tags.
        The service supports:

        - Multiple target devices
        - Custom content with text, shapes, and images
        - Background color and rotation
        - Dithering options
        - "Dry run" mode for testing

        Args:
            service: Service call object with parameters and target devices

        Raises:
            HomeAssistantError: If AP is offline or image generation fails
        """
        try:
            is_ble = is_ble_device(hass, entity_id)

            # For hub devices, ensure hub is online
            hub = None
            if not is_ble:
                hub = get_hub_from_hass(hass)
                if not hub.online:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="ap_offline",
                    )

            # Generate image
            width, height, accent_color = await _get_tag_dimensions(hass, entity_id, is_ble)
            rotate = service.data.get("rotate", 0)
            img = await generate_image(
                width=width,
                height=height,
                elements=service.data.get("payload", []),
                background=service.data.get("background", "white"),
                accent_color=accent_color,
                session=async_get_clientsession(hass),
                data_provider=HADataProvider(hass),
            )
            if rotate:
                img = img.rotate(rotate, expand=True)
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality="maximum")
            image_data = buf.getvalue()

            # Handle dry-run mode
            if service.data.get("dry-run", False):
                _LOGGER.info("Dry run completed for %s", entity_id)
                tag_mac = get_mac_from_entity_id(entity_id)
                async_dispatcher_send(
                    hass,
                    f"{SIGNAL_TAG_IMAGE_UPDATE}_{tag_mac}",
                    image_data
                )
                return

            # Upload image
            dither_mode = _parse_dither_mode(service.data.get("dither", "ordered"))

            refresh_type = int(service.data.get("refresh_type", 0))

            if is_ble:
                from .util import is_bluetooth_available
                if not is_bluetooth_available(hass):
                    raise ServiceValidationError(
                        translation_domain=DOMAIN,
                        translation_key="ble_upload_bt_disabled",
                        translation_placeholders={"entity_id": entity_id},
                    )

                mac = get_mac_from_entity_id(entity_id)

                protocol_type = "atc"
                for entry in hass.config_entries.async_entries(DOMAIN):
                    runtime_data = getattr(entry, 'runtime_data', None)
                    if runtime_data is not None and is_ble_entry(runtime_data):
                        if runtime_data.mac_address.upper() == mac:
                            protocol_type = runtime_data.protocol_type
                            break

                if protocol_type == "open_display":
                    await ble_upload_queue.add_to_queue(
                        upload_to_opendisplay, hass, entity_id, image_data, dither_mode, refresh_type
                    )
                else:
                    await ble_upload_queue.add_to_queue(upload_to_atc_ble, hass, entity_id, image_data, dither_mode)
            else:
                # Map refresh_type to AP's lut parameter
                # 0→1 (full), 1→3 (fast), 2→2 (fast no-reds), 3→0 (no-repeats)
                ap_lut_mapping = {0: 1, 1: 3, 2: 2, 3: 0}
                ap_lut = ap_lut_mapping.get(refresh_type, 1)  # Default to 1 (full) if invalid
                await hub_upload_queue.add_to_queue(
                    upload_to_hub, hub, entity_id, image_data, dither_mode.value,
                    service.data.get("ttl", 60),
                    service.data.get("preload_type", 0),
                    service.data.get("preload_lut", 0),
                    ap_lut
                )

        except ServiceValidationError:
            raise  # User input errors - propagate unchanged
        except HomeAssistantError:
            raise  # Operational errors - propagate unchanged
        except Exception as err:
            # Unexpected errors - wrap as operational error
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="error_processing_device",
                translation_placeholders={"entity_id": entity_id, "error": str(err)}
            ) from err



    @require_hub_online
    @handle_targets
    async def setled_service(service: ServiceCall, entity_id: str, hub: Hub) -> None:
        pattern = _build_led_pattern(service.data)

        await hub.set_led_pattern(entity_id, pattern)

    @require_hub_online
    @handle_targets
    async def clear_pending_service(service: ServiceCall, entity_id: str, hub: Hub) -> None:
        """Clear pending updates for target devices."""
        await hub.send_tag_cmd(entity_id, "clear")

    @require_hub_online
    @handle_targets
    async def force_refresh_service(service: ServiceCall, entity_id: str, hub: Hub) -> None:
        """Force refresh target devices."""
        await hub.send_tag_cmd(entity_id, "refresh")

    @require_hub_online
    @handle_targets
    async def reboot_tag_service(service: ServiceCall,entity_id: str, hub: Hub) -> None:
        """Reboot target devices."""
        await hub.send_tag_cmd(entity_id, "reboot")

    @require_hub_online
    @handle_targets
    async def scan_channels_service(service: ServiceCall, entity_id: str, hub: Hub) -> None:
        """Trigger channel scan on target devices."""
        await hub.send_tag_cmd(entity_id, "scan")

    @require_hub_online
    async def reboot_ap_service(service: ServiceCall, hub: Hub) -> None:
        """Reboot the Access Point."""
        await hub.reboot_ap()

    # Register all services
    hass.services.async_register(DOMAIN, "drawcustom", drawcustom_service)
    hass.services.async_register(DOMAIN, "setled", setled_service)
    hass.services.async_register(DOMAIN, "clear_pending", clear_pending_service)
    hass.services.async_register(DOMAIN, "force_refresh", force_refresh_service)
    hass.services.async_register(DOMAIN, "reboot_tag", reboot_tag_service)
    hass.services.async_register(DOMAIN, "scan_channels", scan_channels_service)
    hass.services.async_register(DOMAIN, "reboot_ap", reboot_ap_service)
