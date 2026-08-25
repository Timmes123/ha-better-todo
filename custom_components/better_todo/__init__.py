"""The Better ToDo integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change
from homeassistant.loader import async_get_integration

from .const import DOMAIN, FEATURE_CALENDAR, FEATURE_TODO_MIRROR
from .frontend import async_setup_frontend
from .manager import BetterTodoManager
from .services import async_register_services, async_remove_services
from .websocket_api import async_register_websocket

_LOGGER = logging.getLogger(__name__)

PLATFORMS_KEY = f"{DOMAIN}_platforms"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Better ToDo from a config entry."""
    manager = BetterTodoManager(hass, entry)
    await manager.async_load()
    hass.data[DOMAIN] = manager

    async_register_websocket(hass)
    async_register_services(hass)

    features = manager.features
    platforms = []
    if features.get(FEATURE_TODO_MIRROR):
        platforms.append("todo")
    if features.get(FEATURE_CALENDAR):
        platforms.append("calendar")
    hass.data[PLATFORMS_KEY] = platforms
    if platforms:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)

    integration = await async_get_integration(hass, DOMAIN)
    version = str(integration.version)

    async def _setup_frontend(_event=None) -> None:
        await async_setup_frontend(hass, version)

    if hass.is_running:
        hass.async_create_task(_setup_frontend())
    else:
        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _setup_frontend)
        )

    # Options changes reload the entry via OptionsFlowWithReload (config_flow).
    entry.async_on_unload(
        async_track_time_change(
            hass, manager.async_daily_tick, hour=0, minute=0, second=30
        )
    )
    entry.async_on_unload(
        async_track_time_change(hass, manager.async_minute_tick, second=0)
    )

    manager.notify()
    _LOGGER.info("Better ToDo %s loaded", version)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    platforms = hass.data.pop(PLATFORMS_KEY, [])
    if platforms:
        await hass.config_entries.async_unload_platforms(entry, platforms)
    async_remove_services(hass)
    manager: BetterTodoManager | None = hass.data.pop(DOMAIN, None)
    if manager:
        await manager.async_save_now()
    return True
