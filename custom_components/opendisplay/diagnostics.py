"""Diagnostics support for OpenDisplay."""
from __future__ import annotations

import dataclasses
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .runtime_data import OpenDisplayConfigEntry, OpenDisplayBLERuntimeData

TO_REDACT = {"wifi_ssid", "ip", "encryption_key"}


def _asdict(obj: Any) -> Any:
    """Recursively convert a dataclass to a dict, encoding bytes as hex strings."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _asdict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, bytes):
        return obj.hex()
    if isinstance(obj, list):
        return [_asdict(item) for item in obj]
    return obj


def _clean_mac(mac: str) -> str:
    return mac.replace(":", "").replace("-", "").upper()


def _redact_mac(mac: str) -> str:
    if not mac:
        return "**REDACTED**"
    clean = _clean_mac(mac)
    suffix = clean[-4:] if len(clean) >= 4 else clean
    return f"**REDACTED**{suffix}"


def _redact_name_if_mac(name: str | None, mac: str) -> str | None:
    if not name:
        return name
    if _clean_mac(name) == _clean_mac(mac):
        return _redact_mac(mac)
    return name


async def async_get_config_entry_diagnostics(
        hass: HomeAssistant, entry: OpenDisplayConfigEntry
) -> dict[str, Any]:
    diag: dict[str, Any] = {
        "config_entry": {
            "title": entry.title,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
    }

    runtime_data = entry.runtime_data
    if isinstance(runtime_data, OpenDisplayBLERuntimeData):
        from opendisplay import GlobalConfig
        protocol_type = "open_display" if isinstance(runtime_data.device_config, GlobalConfig) else "atc"
        diag["device_type"] = "ble"
        diag["ble"] = {
            "mac_address": _redact_mac(entry.unique_id),
            "name": _redact_name_if_mac(entry.title, entry.unique_id),
            "protocol_type": protocol_type,
            "device_config": async_redact_data(_asdict(runtime_data.device_config), TO_REDACT),
        }

    return diag
