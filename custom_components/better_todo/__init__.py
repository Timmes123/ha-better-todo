"""The Better ToDo integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .frontend import async_setup_frontend
from .manager import BetterTodoManager
from .services import async_register_services, async_remove_services
from .websocket_api import async_register_websocket

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Better ToDo from a config entry."""
    manager = BetterTodoManager(hass, entry)
    await manager.async_load()
    hass.data[DOMAIN] = manager

    async_register_websocket(hass)
    async_register_services(hass)

    integration = await async_get_integration(hass, DOMAIN)
    version = str(integration.version)

    async def _setup_frontend(_event=None) -> None:
        await async_setup_frontend(hass, version)

    if hass.is_running:
        hass.async_create_task(_setup_frontend())
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _setup_frontend)

    entry.async_on_unload(entry.add_update_listener(_options_updated))
    entry.async_on_unload(
        async_track_time_change(
            hass, manager.async_daily_tick, hour=0, minute=0, second=30
        )
    )

    _LOGGER.info("Better ToDo %s loaded", version)
    return True


async def _options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Push new feature toggles to all connected cards."""
    manager: BetterTodoManager | None = hass.data.get(DOMAIN)
    if manager:
        manager.notify()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    async_remove_services(hass)
    manager: BetterTodoManager | None = hass.data.pop(DOMAIN, None)
    if manager:
        await manager.async_save_now()
    return True
