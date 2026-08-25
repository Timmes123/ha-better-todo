"""WebSocket API for the Better ToDo card."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_UPDATE
from .manager import BetterTodoError, BetterTodoManager

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Register all websocket commands (once per HA run)."""
    if hass.data.get(f"{DOMAIN}_ws_registered"):
        return
    hass.data[f"{DOMAIN}_ws_registered"] = True
    websocket_api.async_register_command(hass, ws_get_data)
    websocket_api.async_register_command(hass, ws_subscribe)
    websocket_api.async_register_command(hass, ws_save_list)
    websocket_api.async_register_command(hass, ws_delete_list)
    websocket_api.async_register_command(hass, ws_save_task)
    websocket_api.async_register_command(hass, ws_delete_task)
    websocket_api.async_register_command(hass, ws_complete_task)
    websocket_api.async_register_command(hass, ws_uncomplete_task)
    websocket_api.async_register_command(hass, ws_skip_task)
    websocket_api.async_register_command(hass, ws_toggle_subtask)


def _manager(hass: HomeAssistant) -> BetterTodoManager:
    manager = hass.data.get(DOMAIN)
    if manager is None:
        raise BetterTodoError("Better ToDo is not set up")
    return manager


def _user_name(connection: websocket_api.ActiveConnection) -> str | None:
    return connection.user.name if connection.user else None


def _handle(func):
    """Wrap a mutation handler with shared error handling."""

    @callback
    def wrapper(hass: HomeAssistant, connection, msg: dict[str, Any]) -> None:
        try:
            result = func(hass, connection, msg)
        except BetterTodoError as err:
            connection.send_error(msg["id"], "better_todo_error", str(err))
            return
        connection.send_result(msg["id"], result)

    return wrapper


@websocket_api.websocket_command({vol.Required("type"): "better_todo/get_data"})
@_handle
def ws_get_data(hass, connection, msg):
    return _manager(hass).serialized_data()


@websocket_api.websocket_command({vol.Required("type"): "better_todo/subscribe"})
@callback
def ws_subscribe(hass, connection, msg):
    manager = _manager(hass)

    @callback
    def push() -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], manager.serialized_data())
        )

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_UPDATE, push
    )
    connection.send_result(msg["id"])
    push()


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/save_list",
        vol.Required("list"): dict,
    }
)
@_handle
def ws_save_list(hass, connection, msg):
    return _manager(hass).save_list(msg["list"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/delete_list",
        vol.Required("list_id"): str,
    }
)
@_handle
def ws_delete_list(hass, connection, msg):
    _manager(hass).delete_list(msg["list_id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/save_task",
        vol.Required("task"): dict,
    }
)
@_handle
def ws_save_task(hass, connection, msg):
    return _manager(hass).save_task(msg["task"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/delete_task",
        vol.Required("task_id"): str,
    }
)
@_handle
def ws_delete_task(hass, connection, msg):
    _manager(hass).delete_task(msg["task_id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/complete_task",
        vol.Required("task_id"): str,
        vol.Optional("all", default=False): bool,
    }
)
@_handle
def ws_complete_task(hass, connection, msg):
    _manager(hass).complete_task(msg["task_id"], msg["all"], _user_name(connection))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/uncomplete_task",
        vol.Required("task_id"): str,
    }
)
@_handle
def ws_uncomplete_task(hass, connection, msg):
    _manager(hass).uncomplete_task(msg["task_id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/skip_task",
        vol.Required("task_id"): str,
    }
)
@_handle
def ws_skip_task(hass, connection, msg):
    _manager(hass).skip_task(msg["task_id"], _user_name(connection))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "better_todo/toggle_subtask",
        vol.Required("task_id"): str,
        vol.Required("subtask_id"): str,
        vol.Required("done"): bool,
    }
)
@_handle
def ws_toggle_subtask(hass, connection, msg):
    _manager(hass).toggle_subtask(msg["task_id"], msg["subtask_id"], msg["done"])
