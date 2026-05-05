import asyncio
import logging
from typing import Any, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
from .runtime_data import OpenDisplayConfigEntry, OpenDisplayBLERuntimeData
from .services import async_setup_services

_LOGGER: Final = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.LIGHT,
    Platform.IMAGE,
    Platform.UPDATE,
]


async def async_migrate_entry(hass: HomeAssistant, entry: OpenDisplayConfigEntry) -> bool:
    """Migrate config entry from VERSION 1 to VERSION 2."""
    if entry.version == 1:
        _LOGGER.info("Migrating OpenDisplay entry %s from version 1 to 2", entry.entry_id)

        old_uid = entry.unique_id or ""
        new_uid = old_uid.removeprefix("opendisplay_ble_")

        new_data = {
            k: v for k, v in entry.data.items()
            if k not in ("mac_address", "name", "device_type")
        }

        entity_registry = er.async_get(hass)
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
            if entity.unique_id and entity.unique_id.startswith("opendisplay_ble_"):
                new_entity_uid = entity.unique_id.removeprefix("opendisplay_ble_")
                entity_registry.async_update_entity(
                    entity.entity_id, new_unique_id=new_entity_uid
                )

        hass.config_entries.async_update_entry(
            entry, unique_id=new_uid, data=new_data, version=2
        )
        _LOGGER.info("Migration complete for %s (unique_id: %s -> %s)", entry.entry_id, old_uid, new_uid)

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: OpenDisplayConfigEntry) -> bool:
    """Migrate config entry from VERSION 1 to VERSION 2."""
    if entry.version == 1:
        _LOGGER.info("Migrating OpenDisplay entry %s from version 1 to 2", entry.entry_id)

        old_uid = entry.unique_id or ""
        new_uid = old_uid.removeprefix("opendisplay_ble_")
        new_data = {
            k: v for k, v in entry.data.items()
            if k not in ("mac_address", "name", "device_type")
        }
        hass.config_entries.async_update_entry(
            entry, unique_id=new_uid, data=new_data, version=2
        )

        @callback
        def migrate_unique_id(entity_entry: er.RegistryEntry) -> dict[str, Any] | None:
            if entity_entry.unique_id and entity_entry.unique_id.startswith("opendisplay_ble_"):
                return {"new_unique_id": entity_entry.unique_id.removeprefix("opendisplay_ble_")}
            return None

        await er.async_migrate_entries(hass, entry.entry_id, migrate_unique_id)
        _LOGGER.info("Migration complete for %s (unique_id: %s -> %s)", entry.entry_id, old_uid, new_uid)

    return True


async def async_remove_clock_mode_buttons(hass: HomeAssistant, entry: ConfigEntry) -> list[str]:
    """Remove deprecated clock mode button entities.

    Clock mode was a tech demo feature that is no longer supported.
    This removes the old button entities from the entity registry.

    Returns:
        list[str]: List of removed button entity IDs
    """
    entity_registry = er.async_get(hass)
    removed_entities = []

    # Find clock mode button entities for this config entry
    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity.unique_id and ("_set_clock_mode" in entity.unique_id or "_disable_clock_mode" in entity.unique_id):
            _LOGGER.info("Removing deprecated clock mode button: %s", entity.entity_id)
            entity_registry.async_remove(entity.entity_id)
            removed_entities.append(entity.entity_id)

    return removed_entities


async def async_remove_invalid_ble_entities(
        hass: HomeAssistant,
        entry: ConfigEntry,
        device_config,
) -> list[str]:
    """Remove BLE entities that are invalid for current device config."""
    from opendisplay import GlobalConfig

    entity_registry = er.async_get(hass)
    removed_entities = []
    mac_address = entry.unique_id

    # For OpenDisplay devices, remove battery sensors if not battery/solar powered
    if isinstance(device_config, GlobalConfig) and device_config.power:
        pm = device_config.power.power_mode
        power_mode = pm.value if hasattr(pm, "value") else int(pm)
        if power_mode not in (1, 3):
            for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
                if entity.unique_id and (
                        f"{mac_address}_battery_percentage" in entity.unique_id or
                        f"{mac_address}_battery_voltage" in entity.unique_id
                ):
                    _LOGGER.info("Removing battery sensor (power_mode=%s): %s", power_mode, entity.entity_id)
                    entity_registry.async_remove(entity.entity_id)
                    removed_entities.append(entity.entity_id)

    return removed_entities



async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the OpenDisplay integration."""

    # Services should be set up unconditionally
    await async_setup_services(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: OpenDisplayConfigEntry) -> bool:
    """Set up OpenDisplay BLE integration from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Configuration Entry object with connection details

    Returns:
        bool: True if setup was successful, False otherwise
    """
    from homeassistant.components import bluetooth
    from homeassistant.components.bluetooth import async_ble_device_from_address
    from datetime import datetime, timezone

    mac_address = entry.unique_id
    name = entry.title
    protocol_type = entry.data.get("protocol_type", "atc")

    # Require device to be advertising before attempting connection
    if not bluetooth.async_address_present(hass, mac_address, connectable=False):
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="ble_device_not_detected",
            translation_placeholders={"name": name, "mac_address": mac_address},
        )

    # Interrogate device for full typed config
    ble_device = async_ble_device_from_address(hass, mac_address, connectable=True)
    if ble_device is None:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="ble_device_not_connectable",
            translation_placeholders={"name": name, "mac_address": mac_address},
        )

    try:
        if protocol_type == "open_display":
            from opendisplay import OpenDisplayDevice, AuthenticationRequiredError
            from opendisplay.exceptions import AuthenticationFailedError
            encryption_key_hex = entry.data.get("encryption_key")
            encryption_key = bytes.fromhex(encryption_key_hex) if encryption_key_hex else None
            async with OpenDisplayDevice(mac_address=mac_address, ble_device=ble_device, encryption_key=encryption_key) as device:
                await device.read_firmware_version()
            device_config = device.config
        else:
            from py_atc_ble_oepl import ATCDevice
            async with ATCDevice(mac_address, ble_device, auto_interrogate=False) as device:
                device_config = await device.interrogate()
    except Exception as err:
        _LOGGER.debug("BLE interrogation failed for %s (%s): %s", name, mac_address, err, exc_info=True)
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="ble_interrogation_failed",
            translation_placeholders={"name": name, "mac_address": mac_address},
        ) from err

    if protocol_type == "open_display":
        from opendisplay.protocol import MANUFACTURER_ID as OD_MANUFACTURER_ID
        adv_manufacturer_id = OD_MANUFACTURER_ID
    else:
        from py_atc_ble_oepl.protocol.constants import MANUFACTURER_ID as ATC_MANUFACTURER_ID
        adv_manufacturer_id = ATC_MANUFACTURER_ID

    ble_data = OpenDisplayBLERuntimeData(
        device_config=device_config,
        protocol_type=protocol_type,
        sensors={},
    )
    entry.runtime_data = ble_data

    if entry.data.get("send_welcome_image", False):
        new_data = dict(entry.data)
        new_data.pop("send_welcome_image", None)
        hass.config_entries.async_update_entry(entry, data=new_data)

        hass.async_create_task(
                _send_welcome_image(
                    hass,
                    entry.entry_id,
                    name,
                )
            )

    def _ble_device_found(
            service_info: bluetooth.BluetoothServiceInfoBleak,
            change: bluetooth.BluetoothChange,
    ) -> None:
        """Handle BLE advertising data updates."""
        if service_info.address != mac_address:
            return

        if protocol_type == "open_display":
            from opendisplay import parse_advertisement, MANUFACTURER_ID as OD_MANUFACTURER_ID
            from opendisplay.battery import voltage_to_percent, CapacityEstimator

            manufacturer_data = service_info.manufacturer_data.get(OD_MANUFACTURER_ID)
            if not manufacturer_data:
                return
            try:
                adv = parse_advertisement(manufacturer_data)
            except Exception as err:
                _LOGGER.debug("Failed to parse OpenDisplay advertisement for %s: %s", mac_address, err)
                return

            sensor_data = {
                "battery_percentage": voltage_to_percent(adv.battery_mv, CapacityEstimator.LI_ION),
                "battery_voltage": adv.battery_mv if adv.battery_mv > 0 else None,
                "rssi": service_info.rssi,
                "last_seen": datetime.now(timezone.utc),
                "temperature": adv.temperature_c,
            }
        else:
            from py_atc_ble_oepl.protocol.constants import MANUFACTURER_ID as ATC_MANUFACTURER_ID
            from py_atc_ble_oepl.protocol.atc import ATCProtocol

            manufacturer_data = service_info.manufacturer_data.get(ATC_MANUFACTURER_ID)
            if not manufacturer_data:
                _LOGGER.debug(
                    "No manufacturer data for 0x%04X on %s",
                    ATC_MANUFACTURER_ID,
                    mac_address,
                )
                return
            try:
                advertising_data = ATCProtocol().parse_advertising_data(manufacturer_data)
                if not advertising_data:
                    return
            except Exception as err:
                _LOGGER.debug("Failed to parse advertising data for %s: %s", mac_address, err, exc_info=True)
                return

            if advertising_data.fw_version:
                from homeassistant.components.bluetooth import CONNECTION_BLUETOOTH
                device_registry = dr.async_get(hass)
                device_entry = device_registry.async_get_device(
                    connections={(CONNECTION_BLUETOOTH, mac_address)}
                )
                new_fw_string = str(advertising_data.fw_version)
                if device_entry and device_entry.sw_version != new_fw_string:
                    device_registry.async_update_device(device_entry.id, sw_version=new_fw_string)

            sensor_data = {
                "battery_percentage": advertising_data.battery_pct,
                "battery_voltage": advertising_data.battery_mv if advertising_data.battery_mv > 0 else None,
                "rssi": service_info.rssi,
                "last_seen": datetime.now(timezone.utc),
                "temperature": advertising_data.temperature,
            }

        for sensor in ble_data.sensors.values():
            sensor.update_from_advertising_data(sensor_data)

    # Remove deprecated clock mode button entities
    removed_clock_buttons = await async_remove_clock_mode_buttons(hass, entry)
    if removed_clock_buttons:
        _LOGGER.info("Removed deprecated clock mode buttons: %s", removed_clock_buttons)

    # Remove invalid entities based on the current device config
    removed_invalid = await async_remove_invalid_ble_entities(hass, entry, device_config)
    if removed_invalid:
        _LOGGER.info("Removed invalid BLE entities: %s", removed_invalid)

    # Set up BLE-specific platforms FIRST (before callback registration)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register BLE advertising listener with protocol-specific manufacturer ID
    unregister_callback = bluetooth.async_register_callback(
        hass,
        _ble_device_found,
        {"manufacturer_id": adv_manufacturer_id},
        bluetooth.BluetoothScanningMode.ACTIVE,
    )

    entry.async_on_unload(unregister_callback)

    return True



async def async_unload_entry(hass: HomeAssistant, entry: OpenDisplayConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Allow manual removal of stale BLE devices."""
    return True




async def _send_welcome_image(
        hass: HomeAssistant,
        entry_id: str,
        device_name: str,
) -> None:
    try:
        for _ in range(10):
            if hass.services.has_service(DOMAIN, "drawcustom"):
                break
            await asyncio.sleep(0.5)
        else:
            _LOGGER.debug("Welcome image: drawcustom service not available")
            return
        device_registry = dr.async_get(hass)
        devices = [
            device
            for device in device_registry.devices.values()
            if entry_id in device.config_entries
        ]
        for _ in range(20):
            devices = dr.async_entries_for_config_entry(device_registry, entry_id)
            if devices:
                device_id = devices[0].id
                break
            await asyncio.sleep(0.5)

        if not device_id:
            _LOGGER.debug("Welcome image: No devices found for entry %s", entry_id)
            return

        device_id = devices[0].id

        entry = hass.config_entries.async_get_entry(entry_id)
        if not entry:
            return

        from opendisplay import GlobalConfig
        from epaper_dithering import ColorScheme

        device_config = entry.runtime_data.device_config
        if isinstance(device_config, GlobalConfig):
            display = device_config.displays[0] if device_config.displays else None
            if not display:
                return
            width = display.pixel_width
            height = display.pixel_height
            cs = display.color_scheme_enum
            color_scheme = cs if isinstance(cs, ColorScheme) else ColorScheme.from_value(cs)
        else:
            width = device_config.width
            height = device_config.height
            color_scheme = ColorScheme.from_value(device_config.color_scheme)

        colors = list(color_scheme.palette.colors.keys())
        use_blue_logo = "blue" in colors
        ha_logo_url = (
            "https://openepaperlink.org/HA_blue.png"
            if use_blue_logo
            else "https://openepaperlink.org/HA_black.png"
        )
        od_logo_url = (
            "https://openepaperlink.org/OpenDisplay.png"
            if use_blue_logo
            else "https://openepaperlink.org/OpenDisplay_black.png"
        )

        title_y_pct = 10
        title_size = max(12, int(height * 0.08))
        logo_y_pct = 40
        logo_size = max(48, int(height * 0.25))
        ha_logo_size = max(32, int(logo_size * 0.8))
        color_box_y_pct = 80
        color_box_size = max(20, int(height * 0.12))

        payload = [
            {
                "type": "text",
                "value": f"Connected to HA {HA_VERSION}",
                "x": "50%",
                "y": f"{title_y_pct}%",
                "size": title_size,
                "color": "black",
                "anchor": "mt",
                "font": "ppb.ttf",
            },
            # Home Assistant logo (left side)
            {
                "type": "dlimg",
                "url": ha_logo_url,
                "x": int(width * 0.35 - ha_logo_size // 2),
                "y": int(height * logo_y_pct / 100 - ha_logo_size // 2),
                "xsize": ha_logo_size,
                "ysize": ha_logo_size,
                "resize_method": "contain",
            },
            # Bluetooth icon (center)
            {
                "type": "icon",
                "value": "mdi:bluetooth-connect",
                "x": "50%",  # Center
                "y": f"{logo_y_pct}%",
                "size": int(logo_size * 0.5),
                "color": "black",
                "anchor": "mm",
            },
            # OpenDisplay logo (right side)
            {
                "type": "dlimg",
                "url": od_logo_url,
                "x": int(width * 0.65 - logo_size // 2),
                "y": int(height * logo_y_pct / 100 - logo_size // 2),
                "xsize": logo_size,
                "ysize": logo_size,
                "resize_method": "contain",
            },
        ]

        num_colors = len(colors)
        spacing = 5
        total_width = num_colors * color_box_size + (num_colors - 1) * spacing
        start_x = (width - total_width) // 2
        box_y = int(height * color_box_y_pct / 100)

        for i, color in enumerate(colors):
            box_x = start_x + i * (color_box_size + spacing)
            payload.append({
                "type": "rectangle",
                "x_start": box_x,
                "y_start": box_y,
                "x_end": box_x + color_box_size,
                "y_end": box_y + color_box_size,
                "fill": color,
                "outline": "black",
                "width": 1,
            })

        _LOGGER.debug("Sending welcome image to %s", device_name)
        await hass.services.async_call(
            DOMAIN,
            "drawcustom",
            {
                "device_id": device_id,
                "payload": payload,
                "background": "white",
                "rotate": 0,
                "dither": 2,
                "ttl": 60,
            },
            blocking=False,
        )

    except Exception as err:
        _LOGGER.debug("Welcome image failed: %s", err, exc_info=True)
