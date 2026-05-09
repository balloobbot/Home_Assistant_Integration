from __future__ import annotations

from datetime import datetime, timedelta
import logging

from awesomeversion import AwesomeVersion
from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import OpenDisplayBLEEntity
from .runtime_data import OpenDisplayBLERuntimeData

_LOGGER = logging.getLogger(__name__)

GITHUB_LATEST_URL = "https://api.github.com/repos/OpenDisplay-org/Firmware/releases/latest"
DEFAULT_RELEASE_URL = "https://github.com/OpenDisplay-org/Firmware/releases"
CACHE_DURATION = timedelta(hours=6)


async def async_setup_entry(
        hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = entry.runtime_data
    if not isinstance(entry_data, OpenDisplayBLERuntimeData):
        return
    from opendisplay import GlobalConfig
    if not isinstance(entry_data.device_config, GlobalConfig):
        return
    async_add_entities([OpenDisplayBleUpdateEntity(hass, entry, entry_data)])


class OpenDisplayBleUpdateEntity(OpenDisplayBLEEntity, UpdateEntity):
    """Firmware update indicator for OpenDisplay tags."""

    _attr_has_entity_name = True
    _attr_translation_key = "firmware"
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    _attr_should_poll = True
    _attr_entity_registry_enabled_default = True

    def __init__(
            self,
            hass: HomeAssistant,
            entry,
            runtime_data: OpenDisplayBLERuntimeData,
    ) -> None:
        self.hass = hass
        self._entry_data = runtime_data
        self._entry = entry
        self._latest_version: str | None = None
        self._release_url: str | None = None
        self._release_notes: str | None = None
        self._last_checked: datetime | None = None
        self._last_fetch_error: str | None = None
        self._session = async_get_clientsession(hass)
        super().__init__(entry)
        self._attr_unique_id = f"{entry.unique_id}_firmware_update"
        self._attr_installed_version = self._compute_installed_version()

    @property
    def available(self) -> bool:
        """Keep the update entity available even if the tag is offline."""
        return True

    def _compute_installed_version(self) -> str | None:
        fw = self._entry.data.get("device_metadata", {}).get("fw_version")
        if fw not in ("", 0, None):
            return str(fw)

        from homeassistant.helpers import device_registry as dr
        from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH

        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device(
            connections={(CONNECTION_BLUETOOTH, self._entry.unique_id)},
        )
        if device and device.sw_version and device.sw_version.lower() != "unknown":
            return device.sw_version

        return None

    @property
    def installed_version(self) -> str | None:
        return self._attr_installed_version

    @property
    def latest_version(self) -> str | None:
        return self._latest_version

    @property
    def release_url(self) -> str | None:
        return self._release_url or DEFAULT_RELEASE_URL

    async def async_release_notes(self) -> str | None:
        return self._release_notes

    async def async_added_to_hass(self) -> None:
        # Ensure we have fresh installed_version and fetch latest once on add
        self._attr_installed_version = self._compute_installed_version()
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Refresh installed_version (in case metadata changed) and latest version from GitHub (cached)."""
        self._attr_installed_version = self._compute_installed_version()

        now = datetime.utcnow()
        if self._last_checked and now - self._last_checked < CACHE_DURATION:
            return

        try:
            async with self._session.get(
                    GITHUB_LATEST_URL,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "HomeAssistant-OpenDisplay-Firmware-update-entity",
                    },
                    raise_for_status=True,
            ) as resp:
                data = await resp.json()

            tag = data.get("tag_name") or data.get("name")
            if not tag:
                _LOGGER.debug("No tag_name/name in GitHub response for %s", self._entry.unique_id)
                return

            normalized = tag[1:] if tag.startswith("v") else tag
            self._latest_version = normalized
            self._release_url = data.get("html_url") or DEFAULT_RELEASE_URL
            self._release_notes = data.get("body")
            self._last_checked = now
            self._last_fetch_error = None
        except Exception as err:
            msg = str(err)
            if msg != self._last_fetch_error:
                _LOGGER.error("Failed to fetch OpenDisplay firmware latest version: %s", msg)
                self._last_fetch_error = msg
            else:
                _LOGGER.debug("Failed to fetch OpenDisplay firmware latest version: %s", msg)

    def version_is_newer(self, latest_version: str, installed_version: str) -> bool:
        """Use AwesomeVersion for comparison."""
        try:
            return AwesomeVersion(latest_version) > AwesomeVersion(installed_version)
        except Exception:
            return latest_version != installed_version
