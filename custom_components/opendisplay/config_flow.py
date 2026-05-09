"""Config flow for OpenDisplay integration."""
from __future__ import annotations

from typing import Any, Final

import voluptuous as vol
from habluetooth.models import BluetoothServiceInfoBleak
from homeassistant import config_entries
from homeassistant.components.bluetooth import async_ble_device_from_address

from .const import DOMAIN, CONF_ENCRYPTION_KEY
import logging

_LOGGER: Final = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenDisplay BLE devices."""

    VERSION = 2

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_device: dict[str, Any] = {}
        self._device_metadata: dict[str, Any] | None = None
        self._encryption_key: str | None = None

    async def async_step_bluetooth(
            self, discovery_info: BluetoothServiceInfoBleak
    ):
        """Handle bluetooth discovery."""
        _LOGGER.debug("BLE Discovery - Name: '%s', Address: %s",
                     discovery_info.name, discovery_info.address)

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info

        from opendisplay.protocol import MANUFACTURER_ID as OD_MANUFACTURER_ID
        from opendisplay import parse_advertisement
        from py_atc_ble_oepl.protocol.constants import MANUFACTURER_ID as ATC_MANUFACTURER_ID
        from py_atc_ble_oepl.protocol.atc import ATCProtocol

        if OD_MANUFACTURER_ID in discovery_info.manufacturer_data:
            protocol_type = "open_display"
            raw = discovery_info.manufacturer_data[OD_MANUFACTURER_ID]
            try:
                adv = parse_advertisement(raw)
                battery_mv = adv.battery_mv
            except Exception as e:
                _LOGGER.error("Failed to parse OpenDisplay advertisement: %s", e)
                return self.async_abort(reason="invalid_advertising_data")
            hw_type = 0
            fw_version = 0
            adv_version = 0
        elif ATC_MANUFACTURER_ID in discovery_info.manufacturer_data:
            protocol_type = "atc"
            raw = discovery_info.manufacturer_data[ATC_MANUFACTURER_ID]
            try:
                atc_adv = ATCProtocol().parse_advertising_data(raw)
                battery_mv = atc_adv.battery_mv
                hw_type = atc_adv.hw_type
                fw_version = atc_adv.fw_version
                adv_version = atc_adv.version
            except Exception as e:
                _LOGGER.error("Failed to parse ATC advertisement: %s", e)
                return self.async_abort(reason="invalid_advertising_data")
        else:
            return self.async_abort(reason="unsupported_protocol")

        device_name = discovery_info.name or f"OpenDisplay_BLE_{discovery_info.address[-8:].replace(':', '')}"

        self._discovered_device = {
            "address": discovery_info.address,
            "name": device_name,
            "rssi": discovery_info.rssi,
            "hw_type": hw_type,
            "battery_mv": battery_mv,
            "fw_version": fw_version,
            "version": adv_version,
            "protocol_type": protocol_type,
        }

        self.context["title_placeholders"] = {"name": device_name}

        try:
            await self._async_interrogate(discovery_info.address)
        except _AuthRequired:
            return await self.async_step_encryption_key()
        except Exception as err:
            _LOGGER.error("BLE interrogation failed during discovery of %s: %s", discovery_info.address, err)
            return self.async_abort(reason="invalid_advertising_data")

        return await self.async_step_bluetooth_confirm()

    async def _async_interrogate(
        self, mac: str, encryption_key: bytes | None = None
    ) -> None:
        """Connect to device via BLE, read config, and store device_metadata."""
        ble_device = async_ble_device_from_address(self.hass, mac, connectable=True)
        if ble_device is None:
            raise Exception(f"No connectable BLE device found for {mac}")

        protocol_type = self._discovered_device["protocol_type"]
        hw_type = self._discovered_device["hw_type"]

        if protocol_type == "atc":
            from py_atc_ble_oepl import ATCDevice
            from py_atc_ble_oepl.models.device_types import get_device_type_name

            async with ATCDevice(mac, ble_device, auto_interrogate=False) as device:
                caps = await device.interrogate()

            model_name = (
                get_device_type_name(device.device_config.screen_type)
                if device.device_config
                else f"ATC 0x{hw_type:04X}"
            )
            self._device_metadata = {
                "hw_type": hw_type,
                "fw_version": self._discovered_device["fw_version"],
                "width": caps.width,
                "height": caps.height,
                "color_scheme": caps.color_scheme,
                "model_name": model_name,
            }
        else:
            from opendisplay import OpenDisplayDevice, AuthenticationRequiredError
            from opendisplay.exceptions import AuthenticationFailedError

            try:
                async with OpenDisplayDevice(
                    mac_address=mac, ble_device=ble_device, encryption_key=encryption_key
                ) as device:
                    fw = await device.read_firmware_version()
            except AuthenticationRequiredError:
                raise _AuthRequired()
            except AuthenticationFailedError:
                raise _AuthFailed()

            device_config = device.config
            if not device_config or not device_config.displays:
                raise ValueError("Invalid device config: no displays")

            display = device_config.displays[0]
            size = (
                f'{display.screen_diagonal_inches:.1f}"'
                if display.screen_diagonal_inches is not None
                else f"{display.pixel_width}x{display.pixel_height}"
            )
            cs_enum = display.color_scheme_enum
            cs_name = str(cs_enum) if isinstance(cs_enum, int) else cs_enum.name

            power_mode = 1
            if device_config.power:
                pm = device_config.power.power_mode
                power_mode = pm.value if hasattr(pm, "value") else int(pm)

            self._device_metadata = {
                "width": display.pixel_width,
                "height": display.pixel_height,
                "color_scheme": display.color_scheme,
                "model_name": f"{size} {cs_name}",
                "fw_version": f"{fw['major']}.{fw['minor']}",
                "power_mode": power_mode,
            }

    async def async_step_bluetooth_confirm(
            self, user_input: dict[str, Any] | None = None
    ):
        """Confirm discovery — interrogation already done in async_step_bluetooth."""
        if user_input is None:
            meta = self._device_metadata or {}
            battery_mv = self._discovered_device.get("battery_mv", 0)
            adv_version = self._discovered_device.get("version", 0)
            return self.async_show_form(
                step_id="bluetooth_confirm",
                description_placeholders={
                    "name": self._discovered_device["name"],
                    "address": self._discovered_device["address"],
                    "rssi": str(self._discovered_device["rssi"]),
                    "battery": f"{battery_mv / 1000:.2f}V" if battery_mv > 0 else "Unknown",
                    "fw_version": str(meta.get("fw_version", "Unknown")),
                    "config_version": str(adv_version) if adv_version > 0 else "Unknown",
                },
            )

        entry_data: dict[str, Any] = {
            "device_metadata": self._device_metadata,
            "protocol_type": self._discovered_device["protocol_type"],
            "send_welcome_image": True,
        }
        if self._encryption_key:
            entry_data[CONF_ENCRYPTION_KEY] = self._encryption_key

        return self.async_create_entry(
            title=self._discovered_device["name"],
            data=entry_data,
        )

    async def async_step_encryption_key(
        self, user_input: dict[str, Any] | None = None
    ):
        """Ask for an encryption key for encrypted OpenDisplay devices."""
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_key = user_input.get(CONF_ENCRYPTION_KEY, "").strip().lower()
            if not raw_key or not all(c in "0123456789abcdef" for c in raw_key) or len(raw_key) != 32:
                errors[CONF_ENCRYPTION_KEY] = "invalid_key_format"
            else:
                try:
                    await self._async_interrogate(
                        self._discovered_device["address"],
                        bytes.fromhex(raw_key),
                    )
                except _AuthFailed:
                    errors[CONF_ENCRYPTION_KEY] = "invalid_auth"
                except Exception as err:
                    _LOGGER.error("Interrogation failed after key entry: %s", err)
                    errors["base"] = "interrogation_failed"
                else:
                    self._encryption_key = raw_key
                    return await self.async_step_bluetooth_confirm()

        return self.async_show_form(
            step_id="encryption_key",
            data_schema=vol.Schema({vol.Required(CONF_ENCRYPTION_KEY): str}),
            description_placeholders={"name": self._discovered_device.get("name", "")},
            errors=errors,
        )


class _AuthRequired(Exception):
    """Device requires an encryption key."""


class _AuthFailed(Exception):
    """Encryption key was rejected by the device."""
