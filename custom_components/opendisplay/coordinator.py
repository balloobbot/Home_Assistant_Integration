from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging

from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothDataUpdateCoordinator,
)
from homeassistant.core import HomeAssistant, callback

_LOGGER = logging.getLogger(__name__)


@dataclass
class BLESensorData:
    battery_percentage: float | None = None
    battery_voltage: int | None = None
    rssi: int | None = None
    last_seen: datetime | None = None
    temperature: float | None = None


class OpenDisplayBLECoordinator(PassiveBluetoothDataUpdateCoordinator[BLESensorData | None]):

    def __init__(self, hass: HomeAssistant, address: str, protocol_type: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            address,
            BluetoothScanningMode.ACTIVE,
            connectable=True,
        )
        self.protocol_type = protocol_type
        self.data: BLESensorData | None = None

    @callback
    def _async_handle_bluetooth_event(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        if self.protocol_type == "open_display":
            self._handle_open_display(service_info)
        else:
            self._handle_atc(service_info)
        super()._async_handle_bluetooth_event(service_info, change)

    def _handle_open_display(self, service_info: BluetoothServiceInfoBleak) -> None:
        from opendisplay import MANUFACTURER_ID, parse_advertisement
        from opendisplay.battery import voltage_to_percent, CapacityEstimator

        manufacturer_data = service_info.manufacturer_data.get(MANUFACTURER_ID)
        if not manufacturer_data:
            return
        try:
            adv = parse_advertisement(manufacturer_data)
        except Exception as err:
            _LOGGER.debug(
                "Failed to parse OpenDisplay advertisement for %s: %s",
                self.address, err,
            )
            return

        self.data = BLESensorData(
            battery_percentage=voltage_to_percent(adv.battery_mv, CapacityEstimator.LI_ION),
            battery_voltage=adv.battery_mv if adv.battery_mv > 0 else None,
            rssi=service_info.rssi,
            last_seen=datetime.now(timezone.utc),
            temperature=adv.temperature_c,
        )

    def _handle_atc(self, service_info: BluetoothServiceInfoBleak) -> None:
        from py_atc_ble_oepl.protocol.constants import MANUFACTURER_ID as ATC_MANUFACTURER_ID
        from py_atc_ble_oepl.protocol.atc import ATCProtocol

        manufacturer_data = service_info.manufacturer_data.get(ATC_MANUFACTURER_ID)
        if not manufacturer_data:
            return
        try:
            advertising_data = ATCProtocol().parse_advertising_data(manufacturer_data)
            if not advertising_data:
                return
        except Exception as err:
            _LOGGER.debug(
                "Failed to parse ATC advertisement for %s: %s",
                self.address, err, exc_info=True,
            )
            return

        if advertising_data.fw_version:
            from homeassistant.helpers import device_registry as dr
            from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
            device_registry = dr.async_get(self.hass)
            device_entry = device_registry.async_get_device(
                connections={(CONNECTION_BLUETOOTH, self.address)}
            )
            new_fw_string = str(advertising_data.fw_version)
            if device_entry and device_entry.sw_version != new_fw_string:
                device_registry.async_update_device(device_entry.id, sw_version=new_fw_string)

        self.data = BLESensorData(
            battery_percentage=advertising_data.battery_pct,
            battery_voltage=advertising_data.battery_mv if advertising_data.battery_mv > 0 else None,
            rssi=service_info.rssi,
            last_seen=datetime.now(timezone.utc),
            temperature=advertising_data.temperature,
        )
