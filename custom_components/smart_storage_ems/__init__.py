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


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register custom Lovelace cards in Home Assistant frontend (once)."""
    flag_key = f"{DOMAIN}_frontend_registered"
    if hass.data.get(flag_key):
        return

    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    cards = [
        ("smart-storage-card.js", "/smart_storage_ems/smart-storage-card.js"),
        ("smart-storage-chart-card.js", "/smart_storage_ems/smart-storage-chart-card.js"),
    ]

    for filename, url_path in cards:
        card_path = os.path.join(frontend_dir, filename)
        if not os.path.exists(card_path):
            continue

        try:
            from homeassistant.components.http import StaticPathConfig
            await hass.http.async_register_static_paths([StaticPathConfig(url_path, card_path, False)])
        except RuntimeError:
            pass
        except (ImportError, AttributeError):
            if hasattr(hass.http, "register_static_path"):
                try:
                    hass.http.register_static_path(url_path, card_path, False)
                except Exception:
                    pass

        try:
            from homeassistant.components.frontend import add_extra_js_url
            add_extra_js_url(hass, url_path)
        except Exception as err:
            _LOGGER.debug("Could not add extra js url for %s: %s", filename, err)

    hass.data[flag_key] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Storage EMS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await _async_register_frontend(hass)

    coordinator = SmartStorageCoordinator(hass, {**entry.data, **entry.options})
    await coordinator.async_setup()

    # Initial data load & schedule periodic 30-min refresh
    await coordinator.async_config_entry_first_refresh()

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
