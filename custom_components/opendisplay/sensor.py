from __future__ import annotations

PARALLEL_UPDATES = 0

from dataclasses import dataclass
from typing import Callable, Any

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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.typing import StateType
import logging

from .entity import OpenDisplayBLEEntity
from .runtime_data import OpenDisplayConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class OpenDisplaySensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any] | None = None
    attr_fn: Callable[[dict], dict] | None = None


BLE_SENSOR_TYPES: tuple[OpenDisplaySensorEntityDescription, ...] = (
    OpenDisplaySensorEntityDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("temperature"),
    ),
    OpenDisplaySensorEntityDescription(
        key="battery_percentage",
        name="Battery Percentage",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("battery_percentage"),
    ),
    OpenDisplaySensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("battery_voltage"),
    ),
    OpenDisplaySensorEntityDescription(
        key="rssi",
        name="RSSI",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("rssi"),
    ),
    OpenDisplaySensorEntityDescription(
        key="last_seen",
        name="Last Seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("last_seen"),
    ),
)


class OpenDisplayBLESensor(OpenDisplayBLEEntity, SensorEntity):
    """BLE sensor entity for OpenDisplay devices."""

    def __init__(
            self,
            hass: HomeAssistant,
            entry: OpenDisplayConfigEntry,
            description: OpenDisplaySensorEntityDescription,
    ) -> None:
        super().__init__(entry)
        self._hass = hass
        self._description = description
        self._sensor_data = {}
        self.entity_description = description
        self._attr_translation_key = description.key

    @property
    def unique_id(self) -> str:
        return f"{self._entry.unique_id}_{self._description.key}"

    @property
    def native_value(self) -> StateType:
        if self._description.value_fn:
            return self._description.value_fn(self._sensor_data)
        return self._sensor_data.get(self._description.key)

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._description.native_unit_of_measurement

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return self._description.device_class

    @property
    def state_class(self) -> SensorStateClass | None:
        return self._description.state_class

    @property
    def entity_category(self) -> EntityCategory | None:
        return self._description.entity_category

    def update_from_advertising_data(self, data: dict) -> None:
        self._sensor_data = data
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        if self._sensor_data:
            self.async_write_ha_state()

    async def async_update(self) -> None:
        pass


async def async_setup_entry(
        hass: HomeAssistant,
        entry: OpenDisplayConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    entry_data = entry.runtime_data
    protocol_type = entry_data.protocol_type

    from opendisplay import GlobalConfig
    device_config = entry_data.device_config

    sensors = []
    for description in BLE_SENSOR_TYPES:
        if description.key in ("battery_percentage", "battery_voltage"):
            if protocol_type == "open_display" and isinstance(device_config, GlobalConfig):
                if device_config.power:
                    pm = device_config.power.power_mode
                    power_mode = pm.value if hasattr(pm, "value") else int(pm)
                    if power_mode not in (1, 3):
                        continue

        sensor = OpenDisplayBLESensor(
            hass=hass,
            entry=entry,
            description=description,
        )
        sensors.append(sensor)
        entry_data.sensors[description.key] = sensor

    async_add_entities(sensors)
