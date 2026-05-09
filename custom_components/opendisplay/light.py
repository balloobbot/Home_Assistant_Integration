from __future__ import annotations

PARALLEL_UPDATES = 1

import asyncio
import logging
from typing import Any

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entity import OpenDisplayBLEEntity
from .runtime_data import OpenDisplayConfigEntry, OpenDisplayBLERuntimeData

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: OpenDisplayConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BLE light entities."""
    # Only create light entity for BLE devices
    entry_data = entry.runtime_data
    if not isinstance(entry_data, OpenDisplayBLERuntimeData):
        return

    # LED only supported on ATC devices
    from opendisplay import GlobalConfig
    if isinstance(entry_data.device_config, GlobalConfig):
        return

    async_add_entities([OpenDisplayBLELight(hass=hass, entry=entry)])


class OpenDisplayBLELight(OpenDisplayBLEEntity, LightEntity):
    """BLE Light entity for OpenDisplay tags."""

    _attr_entity_registry_enabled_default = True

    def __init__(self, hass: HomeAssistant, entry: OpenDisplayConfigEntry) -> None:
        super().__init__(entry)
        self._hass = hass
        self._is_on = False
        self._auto_off_task = None
        self._attr_translation_key = "led"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.unique_id}_light"

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self._is_on

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Return supported color modes."""
        return {ColorMode.ONOFF}

    @property
    def color_mode(self) -> ColorMode:
        """Return current color mode."""
        return ColorMode.ONOFF

    @property
    def supported_features(self) -> LightEntityFeature:
        """Return supported features."""
        return LightEntityFeature(0)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        from homeassistant.components.bluetooth import async_ble_device_from_address
        from py_atc_ble_oepl import ATCDevice
        from py_atc_ble_oepl.protocol.constants import CMD_LED_ON

        try:
            ble_device = async_ble_device_from_address(self.hass, self._entry.unique_id, connectable=True)
            async with ATCDevice(self._entry.unique_id, ble_device, auto_interrogate=False) as dev:
                await dev._connection.write_command(CMD_LED_ON)
            self._is_on = True
            self.async_write_ha_state()
            if self._auto_off_task and not self._auto_off_task.done():
                self._auto_off_task.cancel()
            self._auto_off_task = asyncio.create_task(self._auto_off_timer())
        except Exception as e:
            self.async_write_ha_state()
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="led_on_error",
                translation_placeholders={"error": str(e)},
            ) from e

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        from homeassistant.components.bluetooth import async_ble_device_from_address
        from py_atc_ble_oepl import ATCDevice
        from py_atc_ble_oepl.protocol.constants import CMD_LED_OFF

        try:
            if self._auto_off_task and not self._auto_off_task.done():
                self._auto_off_task.cancel()
            ble_device = async_ble_device_from_address(self.hass, self._entry.unique_id, connectable=True)
            async with ATCDevice(self._entry.unique_id, ble_device, auto_interrogate=False) as dev:
                await dev._connection.write_command(CMD_LED_OFF)
            self._is_on = False
            self.async_write_ha_state()
        except Exception as e:
            self.async_write_ha_state()
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="led_off_error",
                translation_placeholders={"error": str(e)},
            ) from e

    async def async_update(self) -> None:
        """Update the light state."""
        pass

    async def _auto_off_timer(self) -> None:
        """Auto-off timer that turns LED off after BLE connection closes."""
        try:
            await asyncio.sleep(8)
            if self._is_on:
                self._is_on = False
                self.async_write_ha_state()
                _LOGGER.debug("LED auto-turned off for %s after connection closed", self._entry.unique_id)
        except asyncio.CancelledError:
            _LOGGER.debug("Auto-off timer cancelled for %s", self._entry.unique_id)
        except Exception as e:
            _LOGGER.error("Error in auto-off timer for %s: %s", self._entry.unique_id, e)
