"""Calendar entities: one calendar per Better ToDo list.

Tasks with a due date appear in the HA calendar; recurring tasks are expanded
onto every occurrence within the requested window.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import engine
from .const import (
    DOMAIN,
    SIGNAL_UPDATE,
    TASK_TYPE_AFTER_COMPLETION,
    TASK_TYPE_SCHEDULED,
    TASK_TYPE_SIMPLE,
)
from .manager import BetterTodoManager

MAX_EXPANSION = 400


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: BetterTodoManager = hass.data[DOMAIN]
    known: dict[str, BetterTodoCalendarEntity] = {}
    registry = er.async_get(hass)

    @callback
    def sync_lists() -> None:
        current = {lst["id"]: lst for lst in manager.data["lists"]}
        if current.keys() == known.keys():
            return  # no list added/removed; renames are handled per entity
        added = [
            BetterTodoCalendarEntity(manager, lst)
            for list_id, lst in current.items()
            if list_id not in known
        ]
        for entity in added:
            known[entity.list_id] = entity
        if added:
            async_add_entities(added)
        for list_id in list(known):
            if list_id not in current:
                known.pop(list_id)
        # Deleting the registry entry also removes the live entity; without
        # this the entry lingers as an unavailable orphan after list deletion.
        valid = {f"{DOMAIN}_{list_id}_calendar" for list_id in current}
        for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
            if reg_entry.domain == "calendar" and reg_entry.unique_id not in valid:
                registry.async_remove(reg_entry.entity_id)

    sync_lists()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_UPDATE, sync_lists))


class BetterTodoCalendarEntity(CalendarEntity):
    """Calendar view of one Better ToDo list."""

    _attr_should_poll = False

    def __init__(self, manager: BetterTodoManager, lst: dict) -> None:
        self.manager = manager
        self.list_id = lst["id"]
        self._attr_unique_id = f"{DOMAIN}_{lst['id']}_calendar"
        self._attr_name = f"{lst['name']} Kalender"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATE, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        lst = next(
            (l for l in self.manager.data["lists"] if l["id"] == self.list_id), None
        )
        if lst:
            self._attr_name = f"{lst['name']} Kalender"
        self.async_write_ha_state()

    @property
    def event(self) -> CalendarEvent | None:
        # Called on every state write: find just the next occurrence per task
        # instead of expanding a full year of events.
        today = dt_util.now().date()
        best_task = None
        best_key = None
        for task in self.manager.data["tasks"]:
            if task["list_id"] != self.list_id:
                continue
            day = self._next_occurrence(task, today)
            if day is None:
                continue
            # Tie-break same-day events by due_time; all-day ("") sorts first,
            # matching the old expanded-list string sort.
            key = (day, str(task.get("due_time") or ""))
            if best_key is None or key < best_key:
                best_task, best_key = task, key
        return self._make_event(best_task, best_key[0]) if best_task else None

    def _next_occurrence(self, task: dict, today: date) -> date | None:
        """The task's next occurrence on/after today, or None."""
        if task.get("ended"):
            return None
        try:
            due = engine.parse_date(task.get("due_date"))
            if due is None:
                return None
            typ = task.get("type", TASK_TYPE_SIMPLE)
            if typ == TASK_TYPE_SCHEDULED:
                sched = task.get("schedule") or {}
                until = engine.parse_date(sched.get("until"))
                # due_info returns the first occurrence after the passed day,
                # so "yesterday" yields the next occurrence on/after today —
                # same stepping logic as everywhere else, not a re-implementation.
                _count, nxt = engine.due_info(due, sched, today - timedelta(days=1))
                if nxt < today or (until and nxt > until):
                    return None
                return nxt
            if typ in (TASK_TYPE_SIMPLE, TASK_TYPE_AFTER_COMPLETION):
                if task.get("status") == "done":
                    return None
                if typ == TASK_TYPE_AFTER_COMPLETION:
                    due = engine.interval_first_active(due, task.get("interval") or {})
                return due if due >= today else None
        except (ValueError, TypeError, KeyError):
            return None
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return self._events_between(start_date.date(), end_date.date())

    def _events_between(self, start: date, end: date) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for task in self.manager.data["tasks"]:
            if task["list_id"] != self.list_id or task.get("ended"):
                continue
            typ = task.get("type", TASK_TYPE_SIMPLE)
            try:
                due = engine.parse_date(task.get("due_date"))
            except (ValueError, TypeError):
                continue
            if due is None:
                continue
            if typ == TASK_TYPE_SCHEDULED:
                try:
                    sched = task.get("schedule") or {}
                    until = engine.parse_date(sched.get("until"))
                    d = due
                    for _ in range(MAX_EXPANSION):
                        if d > end or (until and d > until):
                            break
                        if d >= start:
                            events.append(self._make_event(task, d))
                        d = engine.advance(d, sched)
                except (ValueError, TypeError, KeyError):
                    continue  # invalid stored rule: skip, never break the calendar
            elif typ in (TASK_TYPE_SIMPLE, TASK_TYPE_AFTER_COMPLETION):
                if task.get("status") == "done":
                    continue
                if typ == TASK_TYPE_AFTER_COMPLETION:
                    due = engine.interval_first_active(due, task.get("interval") or {})
                if start <= due <= end:
                    events.append(self._make_event(task, due))
        events.sort(key=lambda e: str(e.start))
        return events

    def _make_event(self, task: dict, day: date) -> CalendarEvent:
        description = task.get("notes") or None
        if time_str := task.get("due_time"):
            try:
                hour, minute = (int(x) for x in time_str.split(":")[:2])
                start_dt = datetime.combine(
                    day, time(hour, minute), tzinfo=dt_util.get_default_time_zone()
                )
                return CalendarEvent(
                    summary=task["title"],
                    start=start_dt,
                    end=start_dt + timedelta(hours=1),
                    description=description,
                )
            except (ValueError, TypeError):
                pass
        return CalendarEvent(
            summary=task["title"],
            start=day,
            end=day + timedelta(days=1),
            description=description,
        )
