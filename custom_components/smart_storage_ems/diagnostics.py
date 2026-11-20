"""Diagnostics support for Smart Storage EMS."""

from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SmartStorageCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: SmartStorageCoordinator = hass.data[DOMAIN][entry.entry_id]
    return coordinator.get_diagnostics_data()
