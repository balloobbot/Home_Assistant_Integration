from __future__ import annotations

PARALLEL_UPDATES = 0

from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
import logging

from .coordinator import OpenDisplayBLECoordinator, BLESensorData
from .runtime_data import OpenDisplayConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class OpenDisplaySensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[BLESensorData], Any] | None = None


BLE_SENSOR_TYPES: tuple[OpenDisplaySensorEntityDescription, ...] = (
    OpenDisplaySensorEntityDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.temperature,
    ),
    OpenDisplaySensorEntityDescription(
        key="battery_percentage",
        name="Battery Percentage",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.battery_percentage,
    ),
    OpenDisplaySensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.battery_voltage,
    ),
    OpenDisplaySensorEntityDescription(
        key="rssi",
        name="RSSI",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.rssi,
    ),
    OpenDisplaySensorEntityDescription(
        key="last_seen",
        name="Last Seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.last_seen,
    ),
)


class OpenDisplayBLESensor(PassiveBluetoothCoordinatorEntity[OpenDisplayBLECoordinator], SensorEntity):
    """BLE sensor entity for OpenDisplay devices."""

    entity_description: OpenDisplaySensorEntityDescription

    def __init__(
        self,
        coordinator: OpenDisplayBLECoordinator,
        description: OpenDisplaySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
        )

    @property
    def native_value(self) -> StateType:
        if self.coordinator.data is None:
            return None
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None


async def async_setup_entry(
        hass: HomeAssistant,
        entry: OpenDisplayConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    entry_data = entry.runtime_data
    coordinator = entry_data.coordinator
    device_config = entry_data.device_config

    from opendisplay import GlobalConfig

    sensors = []
    for description in BLE_SENSOR_TYPES:
        if description.key in ("battery_percentage", "battery_voltage"):
            if isinstance(device_config, GlobalConfig):
                if device_config.power:
                    pm = device_config.power.power_mode
                    power_mode = pm.value if hasattr(pm, "value") else int(pm)
                    if power_mode not in (1, 3):
                        continue
        sensors.append(OpenDisplayBLESensor(coordinator=coordinator, description=description))

    async_add_entities(sensors)
