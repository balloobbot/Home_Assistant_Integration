from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from opendisplay import GlobalConfig
    from py_atc_ble_oepl import DeviceCapabilities
    from .coordinator import OpenDisplayBLECoordinator


@dataclass
class OpenDisplayBLERuntimeData:
    """Runtime data for BLE device entries"""

    device_config: "GlobalConfig | DeviceCapabilities"
    coordinator: "OpenDisplayBLECoordinator"


type OpenDisplayConfigEntry = ConfigEntry[OpenDisplayBLERuntimeData]
