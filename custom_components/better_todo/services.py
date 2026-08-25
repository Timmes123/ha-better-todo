"""Services for Better ToDo automations."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, TASK_TYPES, TASK_TYPE_SIMPLE
from .manager import BetterTodoError, BetterTodoManager

_LOGGER = logging.getLogger(__name__)

SERVICE_ADD_TASK = "add_task"
SERVICE_COMPLETE_TASK = "complete_task"
SERVICE_SKIP_TASK = "skip_task"
SERVICE_REMOVE_TASK = "remove_task"

ADD_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("list"): cv.string,
        vol.Required("title"): cv.string,
        vol.Optional("notes"): cv.string,
        vol.Optional("type", default=TASK_TYPE_SIMPLE): vol.In(TASK_TYPES),
        vol.Optional("due_date"): cv.string,
        vol.Optional("visible_from"): cv.string,
        vol.Optional("assigned_to"): vol.Any(cv.string, [cv.string]),
        vol.Optional("schedule"): dict,
        vol.Optional("interval"): dict,
        vol.Optional("period"): vol.In(["week", "month"]),
    }
)

TASK_REF_SCHEMA = vol.Schema(
    {
        vol.Optional("task_id"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("all", default=False): cv.boolean,
    }
)


def _manager(hass: HomeAssistant) -> BetterTodoManager:
    manager = hass.data.get(DOMAIN)
    if manager is None:
        raise BetterTodoError("Better ToDo is not set up")
    return manager


async def _resolve_by(hass: HomeAssistant, call: ServiceCall) -> str | None:
    if call.context.user_id:
        user = await hass.auth.async_get_user(call.context.user_id)
        if user:
            return user.name
    return None


def _find_task_id(manager: BetterTodoManager, call: ServiceCall) -> str:
    if task_id := call.data.get("task_id"):
        return task_id
    title = (call.data.get("title") or "").strip().casefold()
    if not title:
        raise BetterTodoError("Provide task_id or title")
    for task in manager.data["tasks"]:
        if task["title"].casefold() == title:
            return task["id"]
    raise BetterTodoError(f"No task with title '{call.data.get('title')}'")


@callback
def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_ADD_TASK):
        return

    async def add_task(call: ServiceCall) -> None:
        manager = _manager(hass)
        lst = manager.find_or_create_list(call.data["list"])
        task = {
            "list_id": lst["id"],
            "title": call.data["title"],
            "type": call.data.get("type", TASK_TYPE_SIMPLE),
        }
        for key in ("notes", "due_date", "visible_from", "assigned_to", "schedule", "interval", "period"):
            if key in call.data:
                task[key] = call.data[key]
        manager.save_task(task)

    async def complete_task(call: ServiceCall) -> None:
        manager = _manager(hass)
        manager.complete_task(
            _find_task_id(manager, call),
            bool(call.data.get("all")),
            await _resolve_by(hass, call),
        )

    async def skip_task(call: ServiceCall) -> None:
        manager = _manager(hass)
        manager.skip_task(_find_task_id(manager, call), await _resolve_by(hass, call))

    async def remove_task(call: ServiceCall) -> None:
        manager = _manager(hass)
        manager.delete_task(_find_task_id(manager, call))

    hass.services.async_register(DOMAIN, SERVICE_ADD_TASK, add_task, ADD_TASK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_COMPLETE_TASK, complete_task, TASK_REF_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SKIP_TASK, skip_task, TASK_REF_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_TASK, remove_task, TASK_REF_SCHEMA)


@callback
def async_remove_services(hass: HomeAssistant) -> None:
    for service in (SERVICE_ADD_TASK, SERVICE_COMPLETE_TASK, SERVICE_SKIP_TASK, SERVICE_REMOVE_TASK):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
