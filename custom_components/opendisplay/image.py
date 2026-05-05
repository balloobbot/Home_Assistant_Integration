from __future__ import annotations

PARALLEL_UPDATES = 0

import logging
from datetime import datetime
from typing import Final

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import OpenDisplayBLEEntity
from .runtime_data import OpenDisplayConfigEntry
from .const import DOMAIN, SIGNAL_TAG_IMAGE_UPDATE

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: OpenDisplayConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> bool:
    entry_data = entry.runtime_data
    async_add_entities([
        OpenDisplayBLEImage(
            hass=hass,
            mac_address=entry_data.mac_address,
            name=entry_data.name,
            entry=entry,
        )
    ], True)
    return True


class OpenDisplayBLEImage(OpenDisplayBLEEntity, ImageEntity):
    """Image entity for BLE OpenDisplay devices."""

    _attr_entity_registry_enabled_default = True
    _attr_has_entity_name = True

    def __init__(
            self,
            hass: HomeAssistant,
            mac_address: str,
            name: str,
            entry: OpenDisplayConfigEntry,
    ):
        ImageEntity.__init__(self, hass)
        OpenDisplayBLEEntity.__init__(self, mac_address, name, entry)
        self._attr_translation_key = "content"
        self._attr_unique_id = f"opendisplay_ble_{mac_address}_display_content"
        self._attr_content_type = "image/jpeg"
        self._cached_image: bytes | None = None
        self._last_updated: datetime | None = None

    @property
    def image_last_updated(self) -> datetime | None:
        return self._last_updated

    async def async_image(self) -> bytes | None:
        return self._cached_image

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_TAG_IMAGE_UPDATE}_{self._mac_address}",
                self._handle_image_update,
            )
        )

    @callback
    def _handle_image_update(self, data) -> None:
        if isinstance(data, bytes):
            self._cached_image = data
            self._last_updated = datetime.now()
            self.async_write_ha_state()
