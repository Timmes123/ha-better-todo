"""Data manager for Better ToDo: storage, CRUD, recurrence handling."""

from __future__ import annotations

import copy
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
from homeassistant.components import persistent_notification

from .const import (
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_UNASSIGNED_ALL,
    CONF_SUMMARY_ENABLED,
    CONF_SUMMARY_PERSISTENT,
    CONF_SUMMARY_TIME,
    DEFAULT_FEATURES,
    DEFAULT_REMINDER_TIME,
    DEFAULT_SUMMARY_TIME,
    DOMAIN,
    EVENT_COMPLETED,
    EVENT_CREATED,
    EVENT_DUE,
    EVENT_OVERDUE,
    EVENT_REMINDER,
    MAX_HISTORY,
    SIGNAL_UPDATE,
    SUMMARY_NOTIFICATION_ID,
    SUMMARY_PERIOD_LEAD,
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
        self._summary_sent: date | None = None
        self._persistent_active = False
        self._last_tick: datetime | None = None

    # ------------------------------------------------------------- storage

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        if stored:
            self.data = stored
            self.data.setdefault("lists", [])
            self.data.setdefault("tasks", [])
            self.data.setdefault("history", [])
        # Restore reminder/summary bookkeeping so a restart neither loses
        # reminders that fell into the downtime nor re-sends fired ones.
        # Stored meta is untrusted like everything else: corrupt values fall
        # back to a fresh state instead of failing setup or the minute tick.
        meta = self.data.get("meta") or {}
        try:
            self._fired_reminders = {
                tuple(key) for key in meta.get("fired_reminders") or [] if len(key) == 3
            }
        except (ValueError, TypeError):
            self._fired_reminders = set()
        try:
            self._summary_sent = engine.parse_date(meta.get("summary_sent"))
        except (ValueError, TypeError):
            self._summary_sent = None
        last_tick = meta.get("last_tick")
        try:
            parsed = dt_util.parse_datetime(last_tick) if isinstance(last_tick, str) else None
        except (ValueError, TypeError):
            parsed = None
        # A naive timestamp would make `now - window_start` raise on every
        # tick; better to fall back to the default 10-minute window.
        self._last_tick = parsed if parsed and parsed.tzinfo else None
        if self.normalize():
            self._schedule_save()

    def _meta(self) -> dict:
        return self.data.setdefault("meta", {})

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
        self._refresh_persistent()

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
        fields (assigned_to: str -> list, unpinned monthly day). Returns True
        on change."""
        today = self._today()
        changed = False
        for task in self.data["tasks"]:
            if task.get("type") == TASK_TYPE_PERIOD:
                try:
                    if engine.rollover(task, today):
                        changed = True
                except (ValueError, TypeError):
                    # Corrupt period_start must not fail setup; the task
                    # shows as state "error" via computed_state instead.
                    _LOGGER.exception("Task %s has an invalid period_start", task.get("id"))
            assigned = task.get("assigned_to")
            if isinstance(assigned, str):
                task["assigned_to"] = [assigned] if assigned else []
                changed = True
            elif assigned is None:
                task["assigned_to"] = []
                changed = True
            # Migration: pin the intended day-of-month for stored monthly/
            # yearly rules so short months stop shifting the day permanently.
            if task.get("type") == TASK_TYPE_SCHEDULED and task.get("schedule"):
                try:
                    anchor = engine.parse_date(task.get("due_date"))
                except (ValueError, TypeError):
                    anchor = None
                if anchor and engine.pin_monthly_day(task["schedule"], anchor):
                    changed = True
        return changed

    def computed_state(self, task: dict, today: date) -> dict:
        """compute_state that can never take the whole data set down: a task
        with invalid stored data reports state 'error' instead of raising."""
        try:
            return engine.compute_state(task, today)
        except Exception:  # noqa: BLE001 - one bad task must not break all
            _LOGGER.exception(
                "Task %s (%r) has invalid data", task.get("id"), task.get("title")
            )
            return {"state": "error"}

    # ------------------------------------------------------------- serialization

    def serialized_data(self) -> dict:
        if self.normalize():
            self._schedule_save()
        today = self._today()
        return {
            "features": self.features,
            "lists": sorted(self.data["lists"], key=lambda l: l.get("order", 0)),
            "tasks": [
                {**task, "computed": self.computed_state(task, today)}
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

        # Work on a deep copy: validation canonicalizes nested dicts in
        # place, so a rejected payload must never touch the stored task —
        # not even its schedule/rotation sub-objects.
        task = copy.deepcopy(existing) if existing is not None else self._new_task()
        editable = (
            "list_id", "title", "notes", "type", "priority", "subtasks",
            "assigned_to", "rotation", "visible_from", "due_date", "due_time",
            "lead_days", "schedule", "interval", "period", "order",
            "tags", "reminders", "ended",
        )
        for key in editable:
            if key in data:
                task[key] = data[key]

        self._validate_task(task)

        task["tags"] = sorted({str(t).strip() for t in (task.get("tags") or []) if str(t).strip()})

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
            if task.get("period") not in ("week", "month"):
                task["period"] = "week"
            if not task.get("period_start"):
                task["period_start"] = engine.period_start(
                    task["period"], self._today()
                ).isoformat()
            engine.rollover(task, self._today())

        if existing is None:
            self.data["tasks"].append(task)
            self._fire(EVENT_CREATED, task, None)
        else:
            self.data["tasks"][self.data["tasks"].index(existing)] = task
        self._save_notify()
        return task

    def _validate_task(self, task: dict) -> None:
        """Validate and canonicalize task content before it is persisted.

        Invalid schedules, dates or intervals raise BetterTodoError here —
        once stored they would poison every later compute_state call.
        """
        for key in ("due_date", "visible_from"):
            value = task.get(key)
            if value is None or value == "":
                task[key] = None
                continue
            try:
                task[key] = engine.parse_date(value).isoformat()
            except (ValueError, TypeError) as err:
                raise BetterTodoError(f"Invalid {key}: {value!r}") from err
        due_time = task.get("due_time")
        if due_time:
            parsed = self._parse_hhmm(due_time)
            if parsed is None:
                raise BetterTodoError(f"Invalid due_time: {due_time!r}")
            task["due_time"] = f"{parsed[0]:02d}:{parsed[1]:02d}"
        else:
            task["due_time"] = None
        try:
            if task.get("schedule"):
                engine.validate_schedule(task["schedule"])
                if task.get("due_date"):
                    engine.pin_monthly_day(
                        task["schedule"], engine.parse_date(task["due_date"])
                    )
            if task.get("interval"):
                engine.validate_interval(task["interval"])
        except (ValueError, TypeError, KeyError) as err:
            raise BetterTodoError(f"Invalid schedule/interval: {err}") from err
        try:
            task["reminders"] = sorted(
                {int(r) for r in (task.get("reminders") or []) if int(r) >= 0}
            )[:5]
        except (ValueError, TypeError) as err:
            raise BetterTodoError("Invalid reminders") from err
        for key in ("lead_days", "priority", "order"):
            value = task.get(key)
            if value in (None, ""):
                task[key] = None
                continue
            try:
                task[key] = int(value)
            except (ValueError, TypeError) as err:
                raise BetterTodoError(f"Invalid {key}: {value!r}") from err
        subtasks = task.get("subtasks")
        if subtasks is not None and (
            not isinstance(subtasks, list)
            or any(not isinstance(st, dict) for st in subtasks)
        ):
            raise BetterTodoError("subtasks must be a list of objects")
        rotation = task.get("rotation")
        if rotation is not None and not isinstance(rotation, dict):
            raise BetterTodoError("Invalid rotation")
        if isinstance(rotation, dict):
            persons = rotation.get("persons")
            if persons is not None and (
                not isinstance(persons, list)
                or any(not isinstance(p, str) or not p.strip() for p in persons)
            ):
                raise BetterTodoError("rotation.persons must be a list of person ids")
            try:
                int(rotation.get("index") or 0)  # probe only; save_task normalizes
            except (ValueError, TypeError) as err:
                raise BetterTodoError("Invalid rotation.index") from err

    @staticmethod
    def _parse_hhmm(value) -> tuple[int, int] | None:
        """Parse 'HH:MM[:SS]' into (hour, minute); None when invalid."""
        try:
            hour, minute = (int(x) for x in str(value).split(":")[:2])
        except (ValueError, TypeError):
            return None
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return hour, minute

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
            if task.get("status") == "done":
                return  # already done: no duplicate history entry or event
            task["status"] = "done"
            task["completed_at"] = dt_util.now().isoformat()
        elif typ == TASK_TYPE_SCHEDULED:
            anchor = engine.parse_date(task["due_date"]) or today
            new_anchor, consumed = engine.complete_anchor(
                anchor, task.get("schedule") or {}, today, complete_all
            )
            task["due_date"] = new_anchor.isoformat()
            task["occurrence_count"] = int(task.get("occurrence_count") or 0) + consumed
            if engine.schedule_ended(task, new_anchor):
                task["ended"] = True
            self._rotate(task)
            self._reset_subtasks(task)
        elif typ == TASK_TYPE_AFTER_COMPLETION:
            task["due_date"] = engine.add_interval(today, task.get("interval") or {}).isoformat()
            self._rotate(task)
            self._reset_subtasks(task)
        elif typ == TASK_TYPE_PERIOD:
            rolled = engine.rollover(task, today)
            if task.get("period_done"):
                if rolled:
                    self._save_notify()  # the rollover itself must persist
                return  # already done this period
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
            if task.get("status") != "done":
                return  # nothing to undo; keep history untouched
            task["status"] = "open"
            task["completed_at"] = None
            self._remove_last_complete(task_id)
        elif typ == TASK_TYPE_PERIOD:
            rolled = engine.rollover(task, self._today())
            if not task.get("period_done"):
                if rolled:
                    self._save_notify()  # the rollover itself must persist
                return  # period already rolled over (or never completed)
            task["period_done"] = False
            task["streak"] = max(0, int(task.get("streak") or 0) - 1)
            task["misses"] = int(task.get("prev_misses") or 0)
            # Only a completion from the current period may be dropped —
            # older entries belong to closed periods and must stay.
            self._remove_last_complete(task_id, since=task.get("period_start"))
        else:
            raise BetterTodoError("Only simple and period tasks can be uncompleted")
        self._save_notify()

    def _remove_last_complete(self, task_id: str, since: str | None = None) -> None:
        """Drop the newest 'complete' history entry so statistics stay accurate."""
        for entry in reversed(self.data["history"]):
            if entry["task_id"] == task_id and entry["action"] == "complete":
                if since and str(entry.get("at") or "")[:10] < since:
                    return
                self.data["history"].remove(entry)
                return

    def clear_completed(self, list_ids: list[str] | None = None) -> int:
        """Delete all tasks in the given lists (or all lists) whose display
        state is 'done': completed simple tasks and ended recurring tasks."""
        today = self._today()

        def _done(task: dict) -> bool:
            if list_ids and task["list_id"] not in list_ids:
                return False
            return self.computed_state(task, today).get("state") == "done"

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
        """Fire pending task reminders (checked once per minute).

        The window since the last tick is persisted, so reminders that fall
        into an HA downtime are caught up on the next tick after restart
        (capped at 48 h) instead of being lost. Already-fired keys are
        persisted (debounced): delivery is at-least-once — only a hard crash
        within the save debounce right after a reminder can repeat it.

        meta["last_tick"] is only updated in memory here; it reaches disk
        piggybacked on every real save plus once per daily tick, which keeps
        the idle system free of periodic full-store writes."""
        now = now or dt_util.now()
        today = now.date()
        window_start = self._last_tick or now - timedelta(minutes=10)
        if now - window_start > timedelta(hours=48):
            window_start = now - timedelta(hours=48)
        self._last_tick = now
        self._meta()["last_tick"] = now.isoformat()
        fired_any = False
        await self._async_maybe_send_summary(now, window_start)
        for task in self.data["tasks"]:
            reminders = task.get("reminders") or []
            if not reminders:
                continue
            computed = self.computed_state(task, today)
            due_iso = computed.get("due")
            if not due_iso or computed.get("state") in ("done", "hidden", "error"):
                continue
            due_date = engine.parse_date(due_iso)
            time_str = task.get("due_time") or DEFAULT_REMINDER_TIME
            hour, minute = self._parse_hhmm(time_str) or (9, 0)
            due_dt = datetime.combine(due_date, time(hour, minute), tzinfo=now.tzinfo)
            for offset in reminders:
                offset = int(offset)
                key = (task["id"], offset, due_iso)
                if key in self._fired_reminders:
                    continue
                fire_at = due_dt - timedelta(minutes=offset)
                if window_start < fire_at <= now:
                    self._fired_reminders.add(key)
                    fired_any = True
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
        if fired_any:
            self._persist_reminder_state()

    def _persist_reminder_state(self) -> None:
        self._meta()["fired_reminders"] = [list(key) for key in self._fired_reminders]
        self._schedule_save()

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

    # --------------------------------------------------- daily summary

    def _summary_entries(self, today: date) -> list[tuple[dict, str, dict]]:
        """Open tasks for the daily summary: due/overdue tasks always, period
        tasks only once their period is about to end."""
        entries: list[tuple[dict, str, dict]] = []
        for task in self.data["tasks"]:
            computed = self.computed_state(task, today)
            state = computed.get("state")
            if state in ("due", "overdue"):
                entries.append((task, state, computed))
            elif state == "period_open":
                period = task.get("period") or "week"
                try:
                    start = engine.parse_date(task.get("period_start")) or engine.period_start(period, today)
                except (ValueError, TypeError):
                    start = engine.period_start(period, today)
                days_left = (engine.next_period(period, start) - today).days
                if days_left <= SUMMARY_PERIOD_LEAD.get(period, 2):
                    entries.append((task, "period", computed))
        return entries

    def _summary_line(self, task: dict, kind: str, computed: dict, lang_de: bool) -> str:
        if kind == "overdue":
            n = int(computed.get("due_count") or 1)
            if n > 1:
                suffix = f"{n}× fällig" if lang_de else f"{n}× due"
            else:
                suffix = "überfällig" if lang_de else "overdue"
        elif kind == "due":
            due_time = task.get("due_time")
            if due_time:
                suffix = f"heute {due_time} Uhr" if lang_de else f"today {due_time}"
            else:
                suffix = "heute fällig" if lang_de else "due today"
        else:
            week = (task.get("period") or "week") == "week"
            if lang_de:
                suffix = "noch diese Woche" if week else "noch diesen Monat"
            else:
                suffix = "this week" if week else "this month"
        return f"- {task['title']} ({suffix})"

    def _lang_de(self) -> bool:
        return (self.hass.config.language or "en").lower().startswith("de")

    async def _async_maybe_send_summary(self, now, window_start) -> None:
        options = self.entry.options
        if not options.get(CONF_SUMMARY_ENABLED):
            return
        time_str = options.get(CONF_SUMMARY_TIME) or DEFAULT_SUMMARY_TIME
        hour, minute = self._parse_hhmm(time_str) or (8, 0)
        fire_at = datetime.combine(now.date(), time(hour, minute), tzinfo=now.tzinfo)
        if not (window_start < fire_at <= now):
            return
        if self._summary_sent == now.date():
            return
        self._summary_sent = now.date()
        self._meta()["summary_sent"] = now.date().isoformat()
        self._schedule_save()
        await self._async_send_summary(now.date())

    async def _async_send_summary(self, today: date) -> None:
        options = self.entry.options
        entries = self._summary_entries(today)
        lang_de = self._lang_de()
        targets = options.get(CONF_NOTIFY_TARGETS) or {}
        per_service: dict[str, list[str]] = {}
        for task, kind, computed in entries:
            line = self._summary_line(task, kind, computed, lang_de)
            assigned = task.get("assigned_to") or []
            services = [targets[p] for p in assigned if targets.get(p)]
            if not assigned and options.get(CONF_NOTIFY_UNASSIGNED_ALL):
                services = list(targets.values())
            for service in dict.fromkeys(services):
                per_service.setdefault(service, []).append(line)
        for service, lines in per_service.items():
            n = len(lines)
            if lang_de:
                title = "1 offene Aufgabe" if n == 1 else f"{n} offene Aufgaben"
            else:
                title = "1 open task" if n == 1 else f"{n} open tasks"
            try:
                await self.hass.services.async_call(
                    "notify", service, {"title": title, "message": "\n".join(lines)}
                )
            except Exception:  # noqa: BLE001 - one broken target must not stop the rest
                _LOGGER.exception("Could not send summary via notify.%s", service)
        self._refresh_persistent(force=True)

    @callback
    def _refresh_persistent(self, force: bool = False) -> None:
        """Keep the HA notification-center summary in sync with the data.

        Created/replaced at summary time (force=True); afterwards updated on
        every data change and dismissed once nothing is open any more.
        """
        options = self.entry.options
        if not (options.get(CONF_SUMMARY_ENABLED) and options.get(CONF_SUMMARY_PERSISTENT)):
            return
        if not self._persistent_active and not force:
            return
        lang_de = self._lang_de()
        entries = self._summary_entries(self._today())
        if not entries:
            persistent_notification.async_dismiss(self.hass, SUMMARY_NOTIFICATION_ID)
            self._persistent_active = False
            return
        lines = [self._summary_line(t, k, c, lang_de) for t, k, c in entries]
        persistent_notification.async_create(
            self.hass,
            "\n".join(lines),
            title="Offene Aufgaben" if lang_de else "Open tasks",
            notification_id=SUMMARY_NOTIFICATION_ID,
        )
        self._persistent_active = True

    async def async_daily_tick(self, _now=None) -> None:
        """Midnight housekeeping: roll periods, fire due/overdue events."""
        # Prune fired-reminder keys once their due date is safely in the past
        # (older than the 48 h restart catch-up window can ever look back).
        cutoff = (self._today() - timedelta(days=7)).isoformat()
        pruned = {k for k in self._fired_reminders if str(k[2])[:10] >= cutoff}
        if pruned != self._fired_reminders:
            self._fired_reminders = pruned
            self._persist_reminder_state()
        self.normalize()
        today = self._today()
        for task in self.data["tasks"]:
            computed = self.computed_state(task, today)
            state = computed.get("state")
            if state == "due":
                self._fire(EVENT_DUE, task, None)
            elif state == "overdue":
                self._fire(EVENT_OVERDUE, task, None)
        # One save per day also bounds how stale the persisted last_tick can
        # get on an idle system (the catch-up window tolerates up to 48 h).
        self._schedule_save()
        self.notify()
