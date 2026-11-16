"""Smart Storage EMS Home Assistant Integration."""

import logging
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SmartStorageCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Storage EMS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Register custom Lovelace card static path
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    card_path = os.path.join(frontend_dir, "smart-storage-card.js")
    if os.path.exists(card_path):
        hass.http.register_static_path(
            "/smart_storage_ems/smart-storage-card.js",
            card_path,
            cache_headers=False,
        )

    coordinator = SmartStorageCoordinator(hass, {**entry.data, **entry.options})
    await coordinator.async_setup()

    # Initial data load
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: SmartStorageCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        for unsub in coordinator._unsubscribe_listeners:
            unsub()
    return unload_ok
