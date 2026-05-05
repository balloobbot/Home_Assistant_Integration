from __future__ import annotations

from .const import DOMAIN
import logging
from homeassistant.core import HomeAssistant
from .runtime_data import OpenDisplayBLERuntimeData

_LOGGER = logging.getLogger(__name__)


def is_bluetooth_available(hass: HomeAssistant) -> bool:
    try:
        if "bluetooth" not in hass.config.components:
            return False
        from homeassistant.components import bluetooth
        return bluetooth.async_scanner_count(hass, connectable=True) > 0
    except Exception as err:
        _LOGGER.debug("Bluetooth availability check failed: %s", err)
        return False


def is_ble_entry(entry_data) -> bool:
    return isinstance(entry_data, OpenDisplayBLERuntimeData)


def get_mac_from_entity_id(entity_id: str) -> str:
    return entity_id.split(".")[1].upper()
