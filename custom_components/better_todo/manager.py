"""Data manager for Better ToDo: storage, CRUD, recurrence handling."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import engine
from .const import (
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_UNASSIGNED_ALL,
    DEFAULT_FEATURES,
    DEFAULT_REMINDER_TIME,
    DOMAIN,
    EVENT_COMPLETED,
    EVENT_CREATED,
    EVENT_DUE,
    EVENT_OVERDUE,
    EVENT_REMINDER,
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
        self._fired_reminders: set[tuple[str, int, str]] = set()

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
        """Roll period tasks over into the current period and migrate legacy
        fields (assigned_to: str -> list). Returns True on change."""
        today = self._today()
        changed = False
        for task in self.data["tasks"]:
            if task.get("type") == TASK_TYPE_PERIOD and engine.rollover(task, today):
                changed = True
            assigned = task.get("assigned_to")
            if isinstance(assigned, str):
                task["assigned_to"] = [assigned] if assigned else []
                changed = True
            elif assigned is None:
                task["assigned_to"] = []
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
            "assigned_to", "rotation", "visible_from", "due_date", "due_time",
            "lead_days", "schedule", "interval", "period", "order",
            "tags", "reminders", "ended",
        )
        for key in editable:
            if key in data:
                task[key] = data[key]

        task["tags"] = sorted({str(t).strip() for t in (task.get("tags") or []) if str(t).strip()})
        task["reminders"] = [int(r) for r in (task.get("reminders") or []) if int(r) >= 0][:5]

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
        assigned = task.get("assigned_to")
        if isinstance(assigned, str):
            assigned = [assigned]
        seen: set[str] = set()
        task["assigned_to"] = [
            p for p in (str(p).strip() for p in (assigned or []))
            if p and not (p in seen or seen.add(p))
        ]
        rotation = task.get("rotation")
        if rotation and rotation.get("persons"):
            rotation["index"] = int(rotation.get("index") or 0) % len(rotation["persons"])
            # With rotation active the task is assigned to exactly the
            # current person in the pool.
            task["assigned_to"] = [rotation["persons"][rotation["index"]]]
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
            "assigned_to": [],
            "rotation": None,
            "visible_from": None,
            "due_date": None,
            "due_time": None,
            "lead_days": None,
            "tags": [],
            "reminders": [],
            "occurrence_count": 0,
            "ended": False,
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

    def reorder_tasks(self, list_id: str, task_ids: list[str]) -> None:
        """Apply a manual order to the tasks of one list."""
        position = {task_id: index for index, task_id in enumerate(task_ids)}
        for task in self.data["tasks"]:
            if task["list_id"] == list_id and task["id"] in position:
                task["order"] = position[task["id"]]
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
            task["occurrence_count"] = int(task.get("occurrence_count") or 0) + 1
            if engine.schedule_ended(task, new_anchor):
                task["ended"] = True
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

    def clear_completed(self, list_ids: list[str] | None = None) -> int:
        """Delete all tasks in the given lists (or all lists) whose display
        state is 'done': completed simple tasks and ended recurring tasks."""
        today = self._today()

        def _done(task: dict) -> bool:
            if list_ids and task["list_id"] not in list_ids:
                return False
            return engine.compute_state(task, today).get("state") == "done"

        doomed = {t["id"] for t in self.data["tasks"] if _done(t)}
        if not doomed:
            return 0
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] not in doomed]
        self._save_notify()
        return len(doomed)

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
            task["assigned_to"] = [rotation["persons"][rotation["index"]]]

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

    async def async_minute_tick(self, now=None) -> None:
        """Fire pending task reminders (checked once per minute)."""
        now = now or dt_util.now()
        today = now.date()
        for task in self.data["tasks"]:
            reminders = task.get("reminders") or []
            if not reminders:
                continue
            computed = engine.compute_state(task, today)
            due_iso = computed.get("due")
            if not due_iso or computed.get("state") in ("done", "hidden"):
                continue
            due_date = engine.parse_date(due_iso)
            time_str = task.get("due_time") or DEFAULT_REMINDER_TIME
            try:
                hour, minute = (int(x) for x in time_str.split(":")[:2])
            except (ValueError, TypeError):
                hour, minute = 9, 0
            due_dt = datetime.combine(due_date, time(hour, minute), tzinfo=now.tzinfo)
            for offset in reminders:
                offset = int(offset)
                key = (task["id"], offset, due_iso)
                if key in self._fired_reminders:
                    continue
                fire_at = due_dt - timedelta(minutes=offset)
                if fire_at <= now <= fire_at + timedelta(minutes=10):
                    self._fired_reminders.add(key)
                    self.hass.bus.async_fire(
                        EVENT_REMINDER,
                        {
                            "task_id": task["id"],
                            "title": task["title"],
                            "list_id": task["list_id"],
                            "assigned_to": task.get("assigned_to"),
                            "due": due_iso,
                            "due_time": task.get("due_time"),
                            "offset_minutes": offset,
                        },
                    )
                    await self._async_notify_reminder(task, due_date, offset)

    async def _async_notify_reminder(self, task: dict, due_date, offset: int) -> None:
        """Send the reminder to the notify services configured in the options.

        Assigned persons get their own target; unassigned tasks go to every
        configured target when that option is enabled. No targets configured
        means the events remain the only signal (as before).
        """
        targets = self.entry.options.get(CONF_NOTIFY_TARGETS) or {}
        assigned = task.get("assigned_to") or []
        services = [targets[p] for p in assigned if targets.get(p)]
        if not assigned and self.entry.options.get(CONF_NOTIFY_UNASSIGNED_ALL):
            services = list(targets.values())
        if not services:
            return
        lang_de = (self.hass.config.language or "en").lower().startswith("de")
        date_str = due_date.strftime("%d.%m.%Y") if lang_de else due_date.isoformat()
        due_time = task.get("due_time")
        if lang_de:
            title = "Aufgabe fällig" if offset == 0 else "Erinnerung"
            message = f"{task['title']} — fällig am {date_str}"
            if due_time:
                message += f" um {due_time} Uhr"
        else:
            title = "Task due" if offset == 0 else "Reminder"
            message = f"{task['title']} — due {date_str}"
            if due_time:
                message += f" at {due_time}"
        for service in dict.fromkeys(services):
            try:
                await self.hass.services.async_call(
                    "notify", service, {"title": title, "message": message}
                )
            except Exception:  # noqa: BLE001 - one broken target must not stop the rest
                _LOGGER.exception("Could not send reminder via notify.%s", service)

    async def async_daily_tick(self, _now=None) -> None:
        """Midnight housekeeping: roll periods, fire due/overdue events."""
        if len(self._fired_reminders) > 1000:
            self._fired_reminders.clear()
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
