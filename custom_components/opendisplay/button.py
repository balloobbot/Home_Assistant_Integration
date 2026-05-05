PARALLEL_UPDATES = 1

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers import device_registry as dr
import logging

from .entity import OpenDisplayBLEEntity
from .runtime_data import OpenDisplayConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: OpenDisplayConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    entry_data = entry.runtime_data
    protocol_type = entry_data.protocol_type

    if protocol_type == "open_display":
        async_add_entities([
            RefreshConfigButton(entry_data.mac_address, entry_data.name, entry)
        ])


class RefreshConfigButton(OpenDisplayBLEEntity, ButtonEntity):
    """Button to re-interrogate an OpenDisplay device and update its stored config."""

    _attr_entity_registry_enabled_default = True

    def __init__(self, mac_address: str, name: str, entry: OpenDisplayConfigEntry) -> None:
        super().__init__(mac_address, name, entry)
        self._attr_translation_key = "refresh_config"
        self._attr_unique_id = f"ble_{mac_address}_refresh_config"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Re-interrogate device, update stored metadata and runtime config."""
        from homeassistant.components.bluetooth import async_ble_device_from_address
        from opendisplay import OpenDisplayDevice
        from . import async_remove_invalid_ble_entities

        _LOGGER.info("Refreshing configuration for %s", self._mac_address)

        try:
            encryption_key_hex = self._entry.data.get("encryption_key")
            encryption_key = bytes.fromhex(encryption_key_hex) if encryption_key_hex else None

            ble_device = async_ble_device_from_address(self.hass, self._mac_address, connectable=True)
            if ble_device is None:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="ble_device_not_connectable",
                    translation_placeholders={"name": self._name, "mac_address": self._mac_address},
                )

            async with OpenDisplayDevice(
                mac_address=self._mac_address, ble_device=ble_device, encryption_key=encryption_key
            ) as device:
                fw = await device.read_firmware_version()

            global_config = device.config
            if not global_config or not global_config.displays:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="config_flow_invalid_config",
                )

            display = global_config.displays[0]
            if display.screen_diagonal_inches is not None:
                size = f'{display.screen_diagonal_inches:.1f}"'
            else:
                size = f"{display.pixel_width}x{display.pixel_height}"
            cs_enum = display.color_scheme_enum
            cs_name = str(cs_enum) if isinstance(cs_enum, int) else cs_enum.name
            model_name = f"{size} {cs_name}"

            power_mode = 1
            if global_config.power:
                pm = global_config.power.power_mode
                power_mode = pm.value if hasattr(pm, "value") else int(pm)

            new_metadata = {
                "width": display.pixel_width,
                "height": display.pixel_height,
                "color_scheme": display.color_scheme,
                "model_name": model_name,
                "fw_version": f"{fw['major']}.{fw['minor']}" if fw else self._entry.data.get("device_metadata", {}).get("fw_version"),
                "power_mode": power_mode,
            }

            self.hass.config_entries.async_update_entry(
                self._entry,
                data={**self._entry.data, "device_metadata": new_metadata},
            )
            self._entry.runtime_data.device_config = global_config

            device_registry = dr.async_get(self.hass)
            device = device_registry.async_get_device(identifiers={(DOMAIN, f"ble_{self._mac_address}")})
            if device:
                device_registry.async_update_device(
                    device.id,
                    hw_version=f"{display.pixel_width}x{display.pixel_height}",
                    model=model_name,
                    sw_version=new_metadata.get("fw_version"),
                )

            removed = await async_remove_invalid_ble_entities(self.hass, self._entry, global_config)
            if removed:
                _LOGGER.info("Removed invalid entities after config refresh: %s", removed)

            _LOGGER.info("Reloading integration to apply config changes for %s", self._mac_address)
            await self.hass.config_entries.async_reload(self._entry.entry_id)

        except HomeAssistantError:
            raise
        except Exception as e:
            _LOGGER.error("Failed to refresh configuration for %s: %s", self._mac_address, e)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="refresh_config_failed",
                translation_placeholders={"error": str(e)},
            ) from e
