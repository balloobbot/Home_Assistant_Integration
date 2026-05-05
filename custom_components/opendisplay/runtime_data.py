from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from opendisplay import GlobalConfig
    from py_atc_ble_oepl import DeviceCapabilities


@dataclass
class OpenDisplayBLERuntimeData:
    """Runtime data for BLE device entries"""

    mac_address: str
    name: str
    device_config: "GlobalConfig | DeviceCapabilities"
    protocol_type: str
    sensors: dict[str, Any] = field(default_factory=dict)

type OpenDisplayConfigEntry = ConfigEntry[OpenDisplayBLERuntimeData]