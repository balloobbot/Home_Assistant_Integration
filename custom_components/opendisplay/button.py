PARALLEL_UPDATES = 1

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
import logging

from .entity import OpenDisplayTagEntity, OpenDisplayAPEntity, OpenDisplayBLEEntity
from .runtime_data import OpenDisplayConfigEntry
from .tag_types import get_tag_types_manager
from .util import is_ble_entry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _compare_configs(old: any, new: any, path: str = "") -> list[tuple[str, any, any]]:
    """Recursively compare two configs and return a list of changes.

    Compares two configuration structures (dicts, lists, or values) and identifies
    all fields that have changed between them. Handles nested structures by building
    dot-notation paths (e.g., "power.power_mode") and list indices (e.g., "displays[0].width").

    Args:
        old: Old configuration value (dict, list, or primitive)
        new: New configuration value (dict, list, or primitive)
        path: Current path in the configuration tree (used for recursion)

    Returns:
        List of tuples: (field_path, old_value, new_value) for each changed field
    """
    changes = []

    # Handle None cases
    if old is None and new is None:
        return changes
    if old is None:
        changes.append((path or "root", None, new))
        return changes
    if new is None:
        changes.append((path or "root", old, None))
        return changes

    # If types differ, treat as changed value
    if type(old) is not type(new):
        changes.append((path or "root", old, new))
        return changes

    # Handle dict comparison
    if isinstance(old, dict) and isinstance(new, dict):
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key

            if key not in old:
                # Key added
                changes.append((new_path, None, new[key]))
            elif key not in new:
                # Key removed
                changes.append((new_path, old[key], None))
            else:
                # Key exists in both, recurse
                changes.extend(_compare_configs(old[key], new[key], new_path))
        return changes

    # Handle list comparison
    if isinstance(old, list) and isinstance(new, list):
        max_len = max(len(old), len(new))
        for i in range(max_len):
            new_path = f"{path}[{i}]" if path else f"[{i}]"

            if i >= len(old):
                # Item added
                changes.append((new_path, None, new[i]))
            elif i >= len(new):
                # Item removed
                changes.append((new_path, old[i], None))
            else:
                # Item exists in both, recurse
                changes.extend(_compare_configs(old[i], new[i], new_path))
        return changes

    # Handle primitive values (str, int, float, bool, bytes)
    if old != new:
        changes.append((path or "root", old, new))

    return changes


def _format_value(value: any) -> str:
    """Format a configuration value for logging.

    Converts configuration values to human-readable strings for log output.
    Handles special cases like None, bytes, and large nested structures.

    Args:
        value: Configuration value to format

    Returns:
        Formatted string representation of the value
    """
    if value is None:
        return "None"
    if isinstance(value, bytes):
        # Show hex for bytes, truncate if too long
        hex_str = value.hex()
        return f"0x{hex_str[:16]}..." if len(hex_str) > 16 else f"0x{hex_str}"
    if isinstance(value, (dict, list)):
        # For complex structures, show type and length
        if isinstance(value, dict):
            return f"{{...}} ({len(value)} keys)"
        return f"[...] ({len(value)} items)"
    # For primitives, just convert to string
    return str(value)


async def async_setup_entry(hass: HomeAssistant, entry: OpenDisplayConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up button entities from a config entry.

    Creates button entities based on device type:
    
    For BLE devices:
    - Set clock mode button
    - Disable clock mode button

    For AP devices and tags:
    - Clear pending updates button
    - Force refresh button
    - Reboot tag button
    - Scan channels button
    - Deep sleep button
    - Reboot AP button
    - Refresh tag types button

    Also sets up listeners for new tag discovery and blacklist updates
    to dynamically add and remove buttons as needed.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry
        async_add_entities: Callback to register new entities
    """
    entry_data = entry.runtime_data

    # Check if this is a BLE device
    is_ble_device = is_ble_entry(entry_data)

    if is_ble_device:
        mac_address = entry_data.mac_address
        name = entry_data.name
        protocol_type = entry_data.protocol_type

        ble_buttons = []

        # Add refresh config button for OpenDisplay devices only
        if protocol_type == "open_display":
            ble_buttons.append(
                RefreshConfigButton(mac_address, name, entry)
            )

        async_add_entities(ble_buttons)
        return

    # AP device setup (original logic)
    hub = entry_data

    # Track added tags to prevent duplicates
    added_tags = set()

    async def async_add_tag_buttons(tag_mac: str) -> None:
        """Add buttons for a newly discovered tag.

        Creates and registers button entities for a specific tag:

        - Clear pending updates button
        - Force refresh button
        - Reboot tag button
        - Scan channels button
        - Deep sleep button

        This function is called both during initial setup for existing
        tags and dynamically when new tags are discovered.

        The function includes deduplication logic to prevent creating
        multiple button sets for the same tag, and filtering to avoid
        creating buttons for blacklisted tags.

        Args:
            tag_mac: MAC address of the tag to create buttons for
        """

        # Skip if tag is blacklisted
        if tag_mac in hub.get_blacklisted_tags():
            _LOGGER.debug("Skipping button creation for blacklisted tag: %s", tag_mac)
            return

        if tag_mac in added_tags:
            return

        added_tags.add(tag_mac)
        new_buttons = [
            OpenDisplayTagButton(hass, tag_mac, hub, description)
            for description in TAG_BUTTON_TYPES
        ]
        async_add_entities(new_buttons)

    # Add buttons for existing tags
    for tag_mac in hub.tags:
        await async_add_tag_buttons(tag_mac)

    # Add AP-level buttons
    async_add_entities([
        RebootAPButton(hass, hub),
        RefreshTagTypesButton(hass, hub),
    ])

    # Listen for new tag discoveries
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_tag_discovered",
            async_add_tag_buttons
        )
    )

    # Listen for blacklist updates
    async def handle_blacklist_update() -> None:
        """Handle blacklist updates by removing buttons for blacklisted tags.

        When tags are added to the blacklist, this removes their
        associated button entities and devices from Home Assistant.

        This ensures that blacklisted tags don't appear in the UI
        and don't consume resources in Home Assistant.
        """
        # Get all buttons registered for this entry
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        # Track which devices need to be removed
        devices_to_remove = set()

        # Find and remove entities for blacklisted tags
        entities_to_remove = []
        for entity in entity_registry.entities.values():
            if entity.config_entry_id == entry.entry_id:
                # Check if this entity belongs to a blacklisted tag
                device = device_registry.async_get(entity.device_id) if entity.device_id else None
                if device:
                    for identifier in device.identifiers:
                        if identifier[0] == DOMAIN and identifier[1] in hub.get_blacklisted_tags():
                            entities_to_remove.append(entity.entity_id)
                            # Add device to removal list
                            devices_to_remove.add(device.id)
                            break

        # Remove the entities
        for entity_id in entities_to_remove:
            entity_registry.async_remove(entity_id)
            _LOGGER.debug("Removed entity %s for blacklisted tag", entity_id)

        # Remove the devices
        for device_id in devices_to_remove:
            device_registry.async_remove_device(device_id)
            _LOGGER.debug("Removed device %s for blacklisted tag", device_id)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_blacklist_update",
            handle_blacklist_update
        )
    )


@dataclass(frozen=True, kw_only=True)
class OpenDisplayTagButtonDescription(ButtonEntityDescription):
    """Describes an OpenDisplay tag button."""
    command: str


TAG_BUTTON_TYPES: tuple[OpenDisplayTagButtonDescription, ...] = (
    OpenDisplayTagButtonDescription(
        key="clear_pending",
        translation_key="clear_pending",
        entity_category=EntityCategory.DIAGNOSTIC,
        command="clear",
        entity_registry_enabled_default=True
    ),
    OpenDisplayTagButtonDescription(
        key="force_refresh",
        translation_key="force_refresh",
        entity_category=EntityCategory.DIAGNOSTIC,
        command="refresh",
        entity_registry_enabled_default=True
    ),
    OpenDisplayTagButtonDescription(
        key="reboot_tag",
        translation_key="reboot_tag",
        entity_category=EntityCategory.DIAGNOSTIC,
        command="reboot",
    ),
    OpenDisplayTagButtonDescription(
        key="scan_channels",
        translation_key="scan_channels",
        entity_category=EntityCategory.DIAGNOSTIC,
        command="scan",
    ),
    OpenDisplayTagButtonDescription(
        key="deep_sleep",
        translation_key="deep_sleep",
        entity_category=EntityCategory.DIAGNOSTIC,
        command="deepsleep",
    ),
)


class OpenDisplayTagButton(OpenDisplayTagEntity, ButtonEntity):
    """Generic tag button entity."""

    entity_description: OpenDisplayTagButtonDescription

    def __init__(self, hass: HomeAssistant, tag_mac: str, hub, description: OpenDisplayTagButtonDescription) -> None:
        """Initialize the button entity."""
        super().__init__(hub, tag_mac)
        self.hass = hass
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self.entity_description = description
        self._attr_unique_id = f"{tag_mac}_{description.key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._hub.send_tag_cmd(self._entity_id, self.entity_description.command)


class RebootAPButton(OpenDisplayAPEntity, ButtonEntity):
    """Button to reboot the Access Point."""

    _attr_entity_registry_enabled_default = True

    def __init__(self, hass: HomeAssistant, hub) -> None:
        """Initialize the button entity."""
        super().__init__(hub)
        self.hass = hass
        self._attr_translation_key = "reboot_ap"
        self._attr_unique_id = f"{hub.entry.entry_id}_reboot_ap"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._hub.reboot_ap()


class RefreshTagTypesButton(OpenDisplayAPEntity, ButtonEntity):
    """Button to manually refresh tag types from GitHub."""

    def __init__(self, hass: HomeAssistant, hub) -> None:
        """Initialize the button entity."""
        super().__init__(hub)
        self._hass = hass
        self._attr_translation_key = "refresh_tag_types"
        self._attr_unique_id = f"{hub.entry.entry_id}_refresh_tag_types"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Handle the button press.

        Triggers a refresh of tag type definitions from GitHub
        and displays a notification with the result.

        The refresh process:

        1. Clears the cache timestamp to force a new GitHub fetch
        2. Calls the tag types manager to load the latest definitions
        3. Shows a notification with the number of tag types loaded
        """
        manager = await get_tag_types_manager(self._hass)
        # Force a refresh by clearing the last update timestamp
        manager._last_update = None
        await manager.ensure_types_loaded()
        tag_types_len = len(manager.get_all_types())
        message = f"Successfully refreshed {tag_types_len} tag types from GitHub"
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Tag Types Refreshed",
                "message": message,
                "notification_id": "tag_types_refresh_notification",
            },
        )


class RefreshConfigButton(OpenDisplayBLEEntity, ButtonEntity):
    """Button to re-interrogate an OpenDisplay device and update its stored config."""

    _attr_entity_registry_enabled_default = True

    def __init__(self, mac_address: str, name: str, entry: OpenDisplayConfigEntry) -> None:
        super().__init__(mac_address, name, entry)
        self._attr_translation_key = "refresh_config"
        self._attr_unique_id = f"ble_{mac_address}_refresh_config"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        """Re-interrogate device, update stored metadata and runtime config."""
        from homeassistant.components.bluetooth import async_ble_device_from_address
        from homeassistant.helpers import device_registry as dr
        from opendisplay import OpenDisplayDevice
        from epaper_dithering import ColorScheme
        from . import async_remove_invalid_ble_entities

        _LOGGER.info("Refreshing configuration for %s", self._mac_address)

        try:
            encryption_key_hex = self._entry.data.get("encryption_key")
            encryption_key = bytes.fromhex(encryption_key_hex) if encryption_key_hex else None

            ble_device = async_ble_device_from_address(self.hass, self._mac_address, connectable=True)
            if ble_device is None:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="ble_device_not_connectable",
                    translation_placeholders={"name": self._name, "mac_address": self._mac_address},
                )

            async with OpenDisplayDevice(mac_address=self._mac_address, ble_device=ble_device, encryption_key=encryption_key) as device:
                fw = await device.read_firmware_version()

            global_config = device.config
            if not global_config or not global_config.displays:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="config_flow_invalid_config",
                )

            display = global_config.displays[0]
            if display.screen_diagonal_inches is not None:
                size = f'{display.screen_diagonal_inches:.1f}"'
            else:
                size = f"{display.pixel_width}x{display.pixel_height}"
            cs_enum = display.color_scheme_enum
            cs_name = str(cs_enum) if isinstance(cs_enum, int) else cs_enum.name
            model_name = f"{size} {cs_name}"

            power_mode = 1
            if global_config.power:
                pm = global_config.power.power_mode
                power_mode = pm.value if hasattr(pm, "value") else int(pm)

            new_metadata = {
                "width": display.pixel_width,
                "height": display.pixel_height,
                "color_scheme": display.color_scheme,
                "model_name": model_name,
                "fw_version": f"{fw['major']}.{fw['minor']}" if fw else self._entry.data.get("device_metadata", {}).get("fw_version"),
                "power_mode": power_mode,
            }

            # Persist updated flat metadata
            self.hass.config_entries.async_update_entry(
                self._entry,
                data={**self._entry.data, "device_metadata": new_metadata},
            )

            # Update in-memory runtime config to the fresh GlobalConfig
            self._entry.runtime_data.device_config = global_config

            # Update device registry
            device_registry = dr.async_get(self.hass)
            device = device_registry.async_get_device(identifiers={(DOMAIN, f"ble_{self._mac_address}")})
            if device:
                device_registry.async_update_device(
                    device.id,
                    hw_version=f"{display.pixel_width}x{display.pixel_height}",
                    model=model_name,
                    sw_version=new_metadata.get("fw_version"),
                )

            removed = await async_remove_invalid_ble_entities(self.hass, self._entry, global_config)
            if removed:
                _LOGGER.info("Removed invalid entities after config refresh: %s", removed)

            _LOGGER.info("Reloading integration to apply config changes for %s", self._mac_address)
            await self.hass.config_entries.async_reload(self._entry.entry_id)

        except HomeAssistantError:
            raise
        except Exception as e:
            _LOGGER.error("Failed to refresh configuration for %s: %s", self._mac_address, e)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="refresh_config_failed",
                translation_placeholders={"error": str(e)},
            ) from e
