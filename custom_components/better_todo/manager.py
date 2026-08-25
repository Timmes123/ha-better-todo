"""Data manager for Better ToDo: storage, CRUD, recurrence handling."""

from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import engine
from .const import (
    DEFAULT_FEATURES,
    DOMAIN,
    EVENT_COMPLETED,
    EVENT_CREATED,
    EVENT_DUE,
    EVENT_OVERDUE,
    MAX_HISTORY,
    SIGNAL_UPDATE,
    TASK_TYPE_AFTER_COMPLETION,
    TASK_TYPE_PERIOD,
    TASK_TYPE_SCHEDULED,
    TASK_TYPE_SIMPLE,
    TASK_TYPES,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
SAVE_DELAY = 2.0


class BetterTodoError(Exception):
    """Raised for invalid operations on the todo data."""


class BetterTodoManager:
    """Owns all Better ToDo data and mutations."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store = Store(hass, STORAGE_VERSION, DOMAIN)
        self.data: dict[str, Any] = {"lists": [], "tasks": [], "history": []}

    # ------------------------------------------------------------- storage

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        if stored:
            self.data = stored
            self.data.setdefault("lists", [])
            self.data.setdefault("tasks", [])
            self.data.setdefault("history", [])
        if self.normalize():
            self._schedule_save()

    async def async_save_now(self) -> None:
        await self._store.async_save(self.data)

    def _schedule_save(self) -> None:
        self._store.async_delay_save(lambda: self.data, SAVE_DELAY)

    @callback
    def notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)

    def _save_notify(self) -> None:
        self._schedule_save()
        self.notify()

    # ------------------------------------------------------------- helpers

    @property
    def features(self) -> dict[str, bool]:
        options = self.entry.options or {}
        return {key: bool(options.get(key, default)) for key, default in DEFAULT_FEATURES.items()}

    def _today(self) -> date:
        return dt_util.now().date()

    def _list(self, list_id: str) -> dict | None:
        return next((l for l in self.data["lists"] if l["id"] == list_id), None)

    def _task(self, task_id: str) -> dict:
        task = next((t for t in self.data["tasks"] if t["id"] == task_id), None)
        if task is None:
            raise BetterTodoError(f"Task {task_id} not found")
        return task

    def normalize(self) -> bool:
        """Roll period tasks over into the current period. Returns True on change."""
        today = self._today()
        changed = False
        for task in self.data["tasks"]:
            if task.get("type") == TASK_TYPE_PERIOD and engine.rollover(task, today):
                changed = True
        return changed

    # ------------------------------------------------------------- serialization

    def serialized_data(self) -> dict:
        if self.normalize():
            self._schedule_save()
        today = self._today()
        return {
            "features": self.features,
            "lists": sorted(self.data["lists"], key=lambda l: l.get("order", 0)),
            "tasks": [
                {**task, "computed": engine.compute_state(task, today)}
                for task in self.data["tasks"]
            ],
            "persons": self._persons(),
        }

    def _persons(self) -> list[dict]:
        return [
            {
                "entity_id": state.entity_id,
                "name": state.name,
                "user_id": state.attributes.get("user_id"),
                "picture": state.attributes.get("entity_picture"),
            }
            for state in sorted(
                self.hass.states.async_all("person"), key=lambda s: s.name or ""
            )
        ]

    # ------------------------------------------------------------- lists

    def save_list(self, data: dict) -> dict:
        name = (data.get("name") or "").strip()
        if not name:
            raise BetterTodoError("List name must not be empty")
        list_id = data.get("id")
        existing = self._list(list_id) if list_id else None
        if existing:
            existing.update(
                {
                    "name": name,
                    "icon": data.get("icon", existing.get("icon")),
                    "color": data.get("color", existing.get("color")),
                }
            )
            result = existing
        else:
            result = {
                "id": uuid.uuid4().hex,
                "name": name,
                "icon": data.get("icon"),
                "color": data.get("color"),
                "order": len(self.data["lists"]),
            }
            self.data["lists"].append(result)
        self._save_notify()
        return result

    def delete_list(self, list_id: str) -> None:
        self.data["lists"] = [l for l in self.data["lists"] if l["id"] != list_id]
        self.data["tasks"] = [t for t in self.data["tasks"] if t["list_id"] != list_id]
        self._save_notify()

    def find_or_create_list(self, name: str) -> dict:
        name = name.strip()
        for lst in self.data["lists"]:
            if lst["name"].casefold() == name.casefold():
                return lst
        return self.save_list({"name": name})

    # ------------------------------------------------------------- tasks

    def save_task(self, data: dict) -> dict:
        title = (data.get("title") or "").strip()
        if not title:
            raise BetterTodoError("Task title must not be empty")
        list_id = data.get("list_id")
        if not list_id or self._list(list_id) is None:
            raise BetterTodoError("Task must belong to an existing list")
        typ = data.get("type") or TASK_TYPE_SIMPLE
        if typ not in TASK_TYPES:
            raise BetterTodoError(f"Unknown task type: {typ}")
        if typ == TASK_TYPE_SCHEDULED and not (data.get("due_date") and data.get("schedule")):
            raise BetterTodoError("Scheduled tasks need due_date and schedule")
        if typ == TASK_TYPE_AFTER_COMPLETION and not (data.get("due_date") and data.get("interval")):
            raise BetterTodoError("After-completion tasks need due_date and interval")

        task_id = data.get("id")
        existing = None
        if task_id:
            existing = next((t for t in self.data["tasks"] if t["id"] == task_id), None)

        task = existing if existing is not None else self._new_task()
        editable = (
            "list_id", "title", "notes", "type", "priority", "subtasks",
            "assigned_to", "rotation", "visible_from", "due_date", "lead_days",
            "schedule", "interval", "period", "order",
        )
        for key in editable:
            if key in data:
                task[key] = data[key]

        # Normalize subtasks and rotation structures.
        task["subtasks"] = [
            {
                "id": st.get("id") or uuid.uuid4().hex,
                "title": (st.get("title") or "").strip(),
                "done": bool(st.get("done")),
            }
            for st in (task.get("subtasks") or [])
            if (st.get("title") or "").strip()
        ]
        rotation = task.get("rotation")
        if rotation and rotation.get("persons"):
            rotation["index"] = int(rotation.get("index") or 0) % len(rotation["persons"])
            if not task.get("assigned_to"):
                task["assigned_to"] = rotation["persons"][rotation["index"]]
        else:
            task["rotation"] = None

        if typ == TASK_TYPE_PERIOD:
            task.setdefault("period", "week")
            if not task.get("period_start"):
                task["period_start"] = engine.period_start(
                    task["period"], self._today()
                ).isoformat()
            engine.rollover(task, self._today())

        if existing is None:
            self.data["tasks"].append(task)
            self._fire(EVENT_CREATED, task, None)
        self._save_notify()
        return task

    def _new_task(self) -> dict:
        return {
            "id": uuid.uuid4().hex,
            "list_id": None,
            "title": "",
            "notes": "",
            "type": TASK_TYPE_SIMPLE,
            "status": "open",
            "completed_at": None,
            "priority": None,
            "subtasks": [],
            "assigned_to": None,
            "rotation": None,
            "visible_from": None,
            "due_date": None,
            "lead_days": None,
            "schedule": None,
            "interval": None,
            "period": None,
            "period_start": None,
            "period_done": False,
            "period_skipped": False,
            "streak": 0,
            "misses": 0,
            "prev_misses": 0,
            "order": len(self.data["tasks"]),
            "created_at": dt_util.now().isoformat(),
        }

    def delete_task(self, task_id: str) -> None:
        self._task(task_id)  # raises if unknown
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        self._save_notify()

    def toggle_subtask(self, task_id: str, subtask_id: str, done: bool) -> None:
        task = self._task(task_id)
        for subtask in task.get("subtasks") or []:
            if subtask["id"] == subtask_id:
                subtask["done"] = done
                self._save_notify()
                return
        raise BetterTodoError(f"Subtask {subtask_id} not found")

    # ------------------------------------------------------------- actions

    def complete_task(self, task_id: str, complete_all: bool = False, by: str | None = None) -> None:
        task = self._task(task_id)
        today = self._today()
        typ = task.get("type", TASK_TYPE_SIMPLE)

        if typ == TASK_TYPE_SIMPLE:
            task["status"] = "done"
            task["completed_at"] = dt_util.now().isoformat()
        elif typ == TASK_TYPE_SCHEDULED:
            anchor = engine.parse_date(task["due_date"]) or today
            new_anchor = engine.complete_anchor(
                anchor, task.get("schedule") or {}, today, complete_all
            )
            task["due_date"] = new_anchor.isoformat()
            self._rotate(task)
            self._reset_subtasks(task)
        elif typ == TASK_TYPE_AFTER_COMPLETION:
            task["due_date"] = engine.add_interval(today, task.get("interval") or {}).isoformat()
            self._rotate(task)
            self._reset_subtasks(task)
        elif typ == TASK_TYPE_PERIOD:
            engine.rollover(task, today)
            if not task.get("period_done"):
                task["prev_misses"] = int(task.get("misses") or 0)
                task["period_done"] = True
                task["period_skipped"] = False
                task["streak"] = int(task.get("streak") or 0) + 1
                task["misses"] = 0

        self._history_add(task, "complete", by)
        self._fire(EVENT_COMPLETED, task, by)
        self._save_notify()

    def uncomplete_task(self, task_id: str) -> None:
        task = self._task(task_id)
        typ = task.get("type", TASK_TYPE_SIMPLE)
        if typ == TASK_TYPE_SIMPLE:
            task["status"] = "open"
            task["completed_at"] = None
        elif typ == TASK_TYPE_PERIOD:
            if task.get("period_done"):
                task["period_done"] = False
                task["streak"] = max(0, int(task.get("streak") or 0) - 1)
                task["misses"] = int(task.get("prev_misses") or 0)
        else:
            raise BetterTodoError("Only simple and period tasks can be uncompleted")
        # Drop the matching history entry so statistics stay accurate.
        for entry in reversed(self.data["history"]):
            if entry["task_id"] == task_id and entry["action"] == "complete":
                self.data["history"].remove(entry)
                break
        self._save_notify()

    def skip_task(self, task_id: str, by: str | None = None) -> None:
        task = self._task(task_id)
        today = self._today()
        typ = task.get("type", TASK_TYPE_SIMPLE)
        if typ == TASK_TYPE_SCHEDULED:
            anchor = engine.parse_date(task["due_date"]) or today
            task["due_date"] = engine.advance(anchor, task.get("schedule") or {}).isoformat()
        elif typ == TASK_TYPE_AFTER_COMPLETION:
            task["due_date"] = engine.add_interval(today, task.get("interval") or {}).isoformat()
        elif typ == TASK_TYPE_PERIOD:
            engine.rollover(task, today)
            task["period_skipped"] = True
            task["period_done"] = False
        else:
            raise BetterTodoError("Simple tasks cannot be skipped")
        self._history_add(task, "skip", by)
        self._save_notify()

    def _rotate(self, task: dict) -> None:
        rotation = task.get("rotation")
        if rotation and rotation.get("persons"):
            rotation["index"] = (int(rotation.get("index") or 0) + 1) % len(rotation["persons"])
            task["assigned_to"] = rotation["persons"][rotation["index"]]

    @staticmethod
    def _reset_subtasks(task: dict) -> None:
        for subtask in task.get("subtasks") or []:
            subtask["done"] = False

    # ------------------------------------------------------------- history / events

    def _history_add(self, task: dict, action: str, by: str | None) -> None:
        self.data["history"].append(
            {
                "id": uuid.uuid4().hex,
                "task_id": task["id"],
                "title": task["title"],
                "list_id": task["list_id"],
                "action": action,
                "at": dt_util.now().isoformat(),
                "by": by,
            }
        )
        if len(self.data["history"]) > MAX_HISTORY:
            self.data["history"] = self.data["history"][-MAX_HISTORY:]

    def _fire(self, event: str, task: dict, by: str | None) -> None:
        self.hass.bus.async_fire(
            event,
            {
                "task_id": task["id"],
                "title": task["title"],
                "list_id": task["list_id"],
                "type": task.get("type"),
                "assigned_to": task.get("assigned_to"),
                "by": by,
            },
        )

    # ------------------------------------------------------------- daily tick

    async def async_daily_tick(self, _now=None) -> None:
        """Midnight housekeeping: roll periods, fire due/overdue events."""
        changed = self.normalize()
        today = self._today()
        for task in self.data["tasks"]:
            computed = engine.compute_state(task, today)
            state = computed.get("state")
            if state == "due":
                self._fire(EVENT_DUE, task, None)
            elif state == "overdue":
                self._fire(EVENT_OVERDUE, task, None)
        if changed:
            self._schedule_save()
        self.notify()
