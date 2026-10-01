"""Services for Better ToDo automations."""

from __future__ import annotations

import copy
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, LOCATION_MODES, MAX_PRIORITY, TASK_TYPES, TASK_TYPE_SIMPLE
from .manager import BetterTodoError, BetterTodoManager

_LOGGER = logging.getLogger(__name__)

SERVICE_ADD_TASK = "add_task"
SERVICE_COMPLETE_TASK = "complete_task"
SERVICE_SKIP_TASK = "skip_task"
SERVICE_REMOVE_TASK = "remove_task"
SERVICE_UPDATE_TASK = "update_task"
SERVICE_GET_TASKS = "get_tasks"

# get_tasks sort modes; without one the stored (card) order is kept.
SORT_PRIORITY = "priority"
SORT_DUE = "due"
SORT_MODES = [SORT_PRIORITY, SORT_DUE]

# Tags, reminders and persons may be passed as a list or comma-separated.
_STR_OR_LIST = vol.Any(cv.string, [cv.string])
_REMINDERS = vol.Any(None, cv.string, [vol.Coerce(int)])
_PRIORITY = vol.Any(None, "", vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_PRIORITY)))
_LOCATION = vol.Any(
    None,
    vol.Schema(
        {
            vol.Required("zone"): cv.string,
            vol.Optional("mode", default="inside"): vol.In(LOCATION_MODES),
        }
    ),
)

ADD_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("list"): cv.string,
        vol.Required("title"): cv.string,
        vol.Optional("notes"): cv.string,
        vol.Optional("type", default=TASK_TYPE_SIMPLE): vol.In(TASK_TYPES),
        vol.Optional("due_date"): cv.string,
        vol.Optional("due_time"): cv.string,
        vol.Optional("visible_from"): cv.string,
        vol.Optional("lead_days"): vol.Any(None, vol.Coerce(int)),
        vol.Optional("assigned_to"): _STR_OR_LIST,
        vol.Optional("schedule"): dict,
        vol.Optional("interval"): dict,
        vol.Optional("period"): vol.In(["week", "month"]),
        vol.Optional("tags"): _STR_OR_LIST,
        vol.Optional("priority"): _PRIORITY,
        vol.Optional("reminders"): _REMINDERS,
        vol.Optional("overdue_repeat"): vol.Any(None, vol.Coerce(int)),
        vol.Optional("location"): _LOCATION,
    }
)

TASK_REF_SCHEMA = vol.Schema(
    {
        vol.Optional("task_id"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("list"): cv.string,
        vol.Optional("all", default=False): cv.boolean,
    }
)

# Fields update_task may change; everything else on the task is kept.
UPDATE_FIELDS = (
    "notes", "type", "due_date", "due_time", "visible_from", "lead_days",
    "assigned_to", "schedule", "interval", "period", "tags", "priority",
    "reminders", "overdue_repeat", "location",
)

UPDATE_TASK_SCHEMA = vol.Schema(
    {
        vol.Optional("task_id"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("list"): cv.string,
        vol.Optional("new_title"): cv.string,
        vol.Optional("new_list"): cv.string,
        vol.Optional("notes"): cv.string,
        vol.Optional("type"): vol.In(TASK_TYPES),
        vol.Optional("due_date"): vol.Any(None, cv.string),
        vol.Optional("due_time"): vol.Any(None, cv.string),
        vol.Optional("visible_from"): vol.Any(None, cv.string),
        vol.Optional("lead_days"): vol.Any(None, vol.Coerce(int)),
        vol.Optional("assigned_to"): vol.Any(None, _STR_OR_LIST),
        vol.Optional("schedule"): dict,
        vol.Optional("interval"): dict,
        vol.Optional("period"): vol.In(["week", "month"]),
        vol.Optional("tags"): vol.Any(None, _STR_OR_LIST),
        vol.Optional("priority"): _PRIORITY,
        vol.Optional("reminders"): _REMINDERS,
        vol.Optional("overdue_repeat"): vol.Any(None, vol.Coerce(int)),
        vol.Optional("location"): _LOCATION,
    }
)

GET_TASKS_SCHEMA = vol.Schema(
    {
        vol.Optional("list"): _STR_OR_LIST,
        vol.Optional("assigned_to"): _STR_OR_LIST,
        vol.Optional("include_unassigned", default=True): cv.boolean,
        vol.Optional("tags"): _STR_OR_LIST,
        # Empty values are accepted so templated scripts can leave a
        # filter blank ("{{ due | default('') }}") without a validation error.
        vol.Optional("status", default="open"): vol.Any(None, "", vol.In(["open", "done", "all"])),
        vol.Optional("due"): vol.Any(None, "", vol.In(["today", "overdue", "week"])),
        vol.Optional("priority"): vol.Any(
            None, "", vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_PRIORITY))
        ),
        vol.Optional("sort"): vol.Any(None, "", vol.In(SORT_MODES)),
    }
)


def _manager(hass: HomeAssistant) -> BetterTodoManager:
    manager = hass.data.get(DOMAIN)
    if manager is None:
        raise BetterTodoError("Better ToDo is not set up")
    return manager


def as_list(value) -> list[str]:
    """'a, b' or ['a', 'b'] -> ['a', 'b'] (trimmed, empties dropped)."""
    if value is None:
        return []
    items = value.split(",") if isinstance(value, str) else list(value)
    return [str(x).strip() for x in items if str(x).strip()]


def normalize_tags(value) -> list[str]:
    """Tags as a list; a leading '#' (as typed in the card) is dropped so
    '#kids' and 'kids' are the same tag."""
    out: list[str] = []
    for tag in as_list(value):
        tag = tag.lstrip("#").strip()
        if tag and tag not in out:
            out.append(tag)
    return out


def as_int_list(value) -> list[int]:
    try:
        return [int(x) for x in as_list(value)]
    except (ValueError, TypeError) as err:
        raise BetterTodoError(f"Invalid reminders: {value!r}") from err


def normalize_fields(data: dict) -> None:
    """Coerce the list-ish service fields into what the manager stores."""
    if "tags" in data:
        data["tags"] = normalize_tags(data["tags"])
    if "reminders" in data:
        data["reminders"] = as_int_list(data["reminders"])
    if "assigned_to" in data and isinstance(data["assigned_to"], str):
        data["assigned_to"] = as_list(data["assigned_to"])


async def _resolve_by(hass: HomeAssistant, call: ServiceCall) -> str | None:
    if call.context.user_id:
        user = await hass.auth.async_get_user(call.context.user_id)
        if user:
            return user.name
    return None


def list_ids(manager: BetterTodoManager, names) -> set[str]:
    """Ids of the lists named (case-insensitive); unknown names raise."""
    ids: set[str] = set()
    for name in as_list(names):
        matches = {
            lst["id"] for lst in manager.data["lists"]
            if lst["name"].casefold() == name.casefold()
        }
        if not matches:
            raise BetterTodoError(f"No list named '{name}'")
        ids |= matches
    return ids


def _find_task_id(manager: BetterTodoManager, call: ServiceCall) -> str:
    if task_id := call.data.get("task_id"):
        return task_id
    title = (call.data.get("title") or "").strip().casefold()
    if not title:
        raise BetterTodoError("Provide task_id or title")
    # An optional list name scopes the title match, so identically named
    # tasks in other lists cannot be hit by accident.
    wanted = list_ids(manager, call.data["list"]) if call.data.get("list") else None
    for task in manager.data["tasks"]:
        if task["title"].casefold() == title and (
            wanted is None or task["list_id"] in wanted
        ):
            return task["id"]
    raise BetterTodoError(f"No task with title '{call.data.get('title')}'")


def person_ids(manager: BetterTodoManager, values) -> set[str]:
    """Accept person entity ids or person names (case-insensitive)."""
    persons = manager.serialized_data()["persons"]
    ids: set[str] = set()
    for value in as_list(values):
        key = value.casefold()
        match = next(
            (p for p in persons if p["entity_id"].casefold() == key or (p["name"] or "").casefold() == key),
            None,
        )
        ids.add(match["entity_id"] if match else value)
    return ids


def query_tasks(manager: BetterTodoManager, data: dict) -> ServiceResponse:
    snapshot = manager.serialized_data()
    lists = {lst["id"]: lst["name"] for lst in snapshot["lists"]}
    persons = {p["entity_id"]: p["name"] for p in snapshot["persons"]}
    wanted_lists = list_ids(manager, data["list"]) if data.get("list") else None
    wanted_persons = person_ids(manager, data["assigned_to"]) if data.get("assigned_to") else None
    wanted_tags = {t.casefold() for t in normalize_tags(data.get("tags"))}
    status = data.get("status") or "open"
    due_filter = data.get("due") or None
    max_priority = data.get("priority") if data.get("priority") not in (None, "") else None
    today = manager._today()
    week_end = (today + timedelta(days=7)).isoformat()

    result = []
    for task in snapshot["tasks"]:
        computed = task.get("computed") or {}
        state = computed.get("state")
        done = state in ("done", "period_done")
        if status == "open" and (done or state in ("hidden", "error")):
            continue
        if status == "done" and not done:
            continue
        if wanted_lists is not None and task["list_id"] not in wanted_lists:
            continue
        assigned = task.get("assigned_to") or []
        if wanted_persons is not None:
            if assigned:
                if not wanted_persons & set(assigned):
                    continue
            elif not data.get("include_unassigned", True):
                continue
        if wanted_tags and not wanted_tags & {t.casefold() for t in task.get("tags") or []}:
            continue
        if max_priority is not None and not (
            task.get("priority") is not None and task["priority"] <= max_priority
        ):
            continue
        due = computed.get("due")
        if due_filter == "overdue" and state != "overdue":
            continue
        if due_filter == "today" and state not in ("due", "overdue"):
            continue
        if due_filter == "week" and not (state == "overdue" or (due and due <= week_end)):
            continue
        result.append(
            {
                "task_id": task["id"],
                "title": task["title"],
                "list": lists.get(task["list_id"], ""),
                "list_id": task["list_id"],
                "type": task.get("type"),
                "period": task.get("period") if task.get("type") == "period" else None,
                "state": state,
                "visible_from": computed.get("visible_from"),
                "done": done,
                "due": due,
                "due_time": task.get("due_time"),
                "days_overdue": computed.get("days_overdue"),
                "days_left": computed.get("days_left"),
                "due_count": computed.get("due_count"),
                "notes": task.get("notes") or "",
                "tags": task.get("tags") or [],
                "priority": task.get("priority"),
                "assigned_to": assigned,
                "assigned_names": [persons.get(p, p) for p in assigned],
                "reminders": task.get("reminders") or [],
                "location": task.get("location"),
                "subtasks": [
                    {"title": st.get("title"), "done": bool(st.get("done"))}
                    for st in task.get("subtasks") or []
                ],
                "streak": task.get("streak") if task.get("type") == "period" else None,
            }
        )
    if sort := data.get("sort"):
        sort_tasks(result, sort)
    return {"count": len(result), "tasks": result}


def sort_tasks(rows: list[dict], mode: str) -> None:
    """Sort get_tasks rows in place: 'priority' = priority, then due date,
    then title; 'due' = due date first. Unset values sort last."""

    def prio(row: dict) -> int:
        return row.get("priority") if row.get("priority") is not None else MAX_PRIORITY + 1

    def due(row: dict) -> str:
        return row.get("due") or "9999-12-31"

    if mode == SORT_DUE:
        rows.sort(key=lambda r: (due(r), prio(r), (r.get("title") or "").casefold()))
    else:
        rows.sort(key=lambda r: (prio(r), due(r), (r.get("title") or "").casefold()))


@callback
def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_ADD_TASK):
        return

    async def add_task(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        lst = manager.find_or_create_list(call.data["list"])
        task = {
            "list_id": lst["id"],
            "title": call.data["title"],
            "type": call.data.get("type", TASK_TYPE_SIMPLE),
        }
        for key in UPDATE_FIELDS:
            if key in call.data:
                task[key] = call.data[key]
        normalize_fields(task)
        saved = manager.save_task(task)
        return {"task_id": saved["id"]}

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

    async def update_task(call: ServiceCall) -> None:
        manager = _manager(hass)
        task_id = _find_task_id(manager, call)
        existing = next(t for t in manager.data["tasks"] if t["id"] == task_id)
        # save_task validates the payload as a whole (e.g. a scheduled task
        # needs due_date + schedule), so start from the full stored task and
        # overlay only the fields that were passed.
        data = copy.deepcopy(existing)
        if "new_title" in call.data:
            data["title"] = call.data["new_title"]
        if "new_list" in call.data:
            data["list_id"] = manager.find_or_create_list(call.data["new_list"])["id"]
        for key in UPDATE_FIELDS:
            if key in call.data:
                data[key] = call.data[key]
        normalize_fields(data)
        # A schedule/interval passed here replaces the stored rule entirely —
        # partial rule edits would silently inherit stale day/weekday fields.
        manager.save_task(data)

    async def get_tasks(call: ServiceCall) -> ServiceResponse:
        return query_tasks(_manager(hass), call.data)

    def _wrap(func):
        # Surface BetterTodoError as a proper service validation error
        # instead of an unhandled exception in the logs.
        async def wrapper(call: ServiceCall):
            try:
                return await func(call)
            except BetterTodoError as err:
                raise ServiceValidationError(str(err)) from err
            except (ValueError, TypeError, KeyError, AttributeError) as err:
                # Legacy tasks stored before input validation can still carry
                # engine-rejected data — return a clean validation error.
                raise ServiceValidationError(f"Invalid task data: {err}") from err

        return wrapper

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_TASK, _wrap(add_task), ADD_TASK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(DOMAIN, SERVICE_COMPLETE_TASK, _wrap(complete_task), TASK_REF_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SKIP_TASK, _wrap(skip_task), TASK_REF_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_TASK, _wrap(remove_task), TASK_REF_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_TASK, _wrap(update_task), UPDATE_TASK_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_GET_TASKS, _wrap(get_tasks), GET_TASKS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


@callback
def async_remove_services(hass: HomeAssistant) -> None:
    for service in (
        SERVICE_ADD_TASK, SERVICE_COMPLETE_TASK, SERVICE_SKIP_TASK,
        SERVICE_REMOVE_TASK, SERVICE_UPDATE_TASK, SERVICE_GET_TASKS,
    ):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
