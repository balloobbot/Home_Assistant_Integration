from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components import bluetooth
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN, OPENDISPLAY_CONFIG_URL, ATC_CONFIG_URL

if TYPE_CHECKING:
    from .runtime_data import OpenDisplayConfigEntry


class OpenDisplayBLEEntity(Entity):
    """Base entity for BLE OpenDisplay devices."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(
            self,
            mac_address: str,
            name: str,
            entry: OpenDisplayConfigEntry,
    ) -> None:
        self._mac_address = mac_address
        self._name = name
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        from opendisplay import GlobalConfig

        runtime = self._entry.runtime_data
        device_config = runtime.device_config
        meta = self._entry.data.get("device_metadata", {})

        if isinstance(device_config, GlobalConfig):
            display = device_config.displays[0] if device_config.displays else None
            width = display.pixel_width if display else 0
            height = display.pixel_height if display else 0
            configuration_url = OPENDISPLAY_CONFIG_URL
        else:
            width = device_config.width
            height = device_config.height
            configuration_url = ATC_CONFIG_URL

        model_name = meta.get("model_name", "Unknown")
        fw_version = meta.get("fw_version")
        if fw_version in (None, "", 0):
            sw_version = None
        elif isinstance(fw_version, int):
            sw_version = f"0x{fw_version:04x}"
        else:
            sw_version = str(fw_version)

        return DeviceInfo(
            identifiers={(DOMAIN, f"ble_{self._mac_address}")},
            name=self._name,
            manufacturer="OpenDisplay",
            model=model_name,
            sw_version=sw_version,
            hw_version=f"{width}x{height}" if width and height else None,
            configuration_url=configuration_url,
        )

    @property
    def available(self) -> bool:
        return bluetooth.async_address_present(self.hass, self._mac_address)
