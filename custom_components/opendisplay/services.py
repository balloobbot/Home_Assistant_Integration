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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from odl_renderer import generate_image

from .const import DOMAIN, SIGNAL_TAG_IMAGE_UPDATE
from epaper_dithering import DitherMode
from .runtime_data import OpenDisplayBLERuntimeData
from .upload import create_upload_queues, upload_to_atc_ble, upload_to_opendisplay
from .util import is_ble_entry, get_mac_from_entity_id, is_bluetooth_available

_LEGACY_DITHER_MAP = {"0": DitherMode.NONE, "1": DitherMode.BURKES, "2": DitherMode.ORDERED}

_LOGGER: Final = logging.getLogger(__name__)


def _parse_dither_mode(value: str) -> DitherMode:
    if str(value) in _LEGACY_DITHER_MAP:
        return _LEGACY_DITHER_MAP[str(value)]
    return DitherMode[str(value).upper()]


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
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ble_no_metadata",
                translation_placeholders={"entity_id": entity_id},
            )
        width = display.pixel_width
        height = display.pixel_height
        cs = display.color_scheme_enum
        color_scheme = cs if isinstance(cs, ColorScheme) else ColorScheme.from_value(cs)
    else:
        width = device_config.width
        height = device_config.height
        color_scheme = ColorScheme.from_value(device_config.color_scheme)

    return width, height, color_scheme.accent_color


async def async_setup_services(hass: HomeAssistant) -> None:
    ble_upload_queue = create_upload_queues()

    async def get_device_ids_from_label_id(label_id: str) -> list[str]:
        device_registry = dr.async_get(hass)
        devices = dr.async_entries_for_label(device_registry, label_id)
        return [
            device.id
            for device in devices
            if any(i[0] == DOMAIN for i in device.identifiers)
        ]

    async def get_device_ids_from_area_id(area_id: str) -> list[str]:
        device_registry = dr.async_get(hass)
        devices = dr.async_entries_for_area(device_registry, area_id)
        return [
            device.id
            for device in devices
            if any(i[0] == DOMAIN for i in device.identifiers)
        ]

    async def get_entity_id_from_device_id(device_id: str) -> str:
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
        mac_address = identifier[4:] if identifier.startswith("ble_") else identifier
        return f"{DOMAIN}.{mac_address.lower()}"

    def handle_targets(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(service: ServiceCall, *args, **kwargs):
            device_ids = service.data.get("device_id", [])
            label_ids = service.data.get("label_id", [])
            area_ids = service.data.get("area_id", [])

            if isinstance(device_ids, str):
                device_ids = [device_ids]
            if isinstance(label_ids, str):
                label_ids = [label_ids]
            if isinstance(area_ids, str):
                area_ids = [area_ids]

            for label_id in label_ids:
                device_ids.extend(await get_device_ids_from_label_id(label_id))
            for area_id in area_ids:
                device_ids.extend(await get_device_ids_from_area_id(area_id))

            seen = set()
            unique_device_ids = [d for d in device_ids if not (d in seen or seen.add(d))]

            if not unique_device_ids:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="no_targets_specified",
                )

            errors: list[tuple[str, str]] = []
            for device_id in unique_device_ids:
                try:
                    entity_id = await get_entity_id_from_device_id(device_id)
                    await func(service, entity_id, *args, **kwargs)
                except ServiceValidationError as err:
                    errors.append((device_id, str(err)))

                try:
                    ble_errors = await ble_upload_queue.wait_for_current_batch()
                    for ble_error in ble_errors:
                        errors.append((device_id, str(ble_error)))
                except (ServiceValidationError, HomeAssistantError) as err:
                    errors.append((device_id, str(err)))

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
        try:
            width, height, accent_color = await _get_ble_tag_dimensions(hass, entity_id)
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

            if service.data.get("dry-run", False):
                _LOGGER.info("Dry run completed for %s", entity_id)
                tag_mac = get_mac_from_entity_id(entity_id)
                async_dispatcher_send(hass, f"{SIGNAL_TAG_IMAGE_UPDATE}_{tag_mac}", image_data)
                return

            dither_mode = _parse_dither_mode(service.data.get("dither", "ordered"))
            refresh_type = int(service.data.get("refresh_type", 0))

            if not is_bluetooth_available(hass):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="ble_upload_bt_disabled",
                    translation_placeholders={"entity_id": entity_id},
                )

            mac = get_mac_from_entity_id(entity_id)
            protocol_type = "atc"
            for entry in hass.config_entries.async_entries(DOMAIN):
                rd = getattr(entry, "runtime_data", None)
                if isinstance(rd, OpenDisplayBLERuntimeData) and rd.mac_address.upper() == mac:
                    protocol_type = rd.protocol_type
                    break

            if protocol_type == "open_display":
                await ble_upload_queue.add_to_queue(
                    upload_to_opendisplay, hass, entity_id, image_data, dither_mode, refresh_type
                )
            else:
                await ble_upload_queue.add_to_queue(
                    upload_to_atc_ble, hass, entity_id, image_data, dither_mode
                )

        except ServiceValidationError:
            raise
        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="error_processing_device",
                translation_placeholders={"entity_id": entity_id, "error": str(err)},
            ) from err

    hass.services.async_register(DOMAIN, "drawcustom", drawcustom_service)
