"""Calendar entities: one calendar per Better ToDo list.

Tasks with a due date appear in the HA calendar; recurring tasks are expanded
onto every occurrence within the requested window.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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

    @callback
    def sync_lists() -> None:
        current = {lst["id"]: lst for lst in manager.data["lists"]}
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
                entity = known.pop(list_id)
                hass.async_create_task(entity.async_remove(force_remove=True))

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
        today = dt_util.now().date()
        events = self._events_between(today, today + timedelta(days=366))
        return events[0] if events else None

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
            due = engine.parse_date(task.get("due_date"))
            if due is None:
                continue
            if typ == TASK_TYPE_SCHEDULED:
                sched = task.get("schedule") or {}
                until = engine.parse_date(sched.get("until"))
                d = due
                for _ in range(MAX_EXPANSION):
                    if d > end or (until and d > until):
                        break
                    if d >= start:
                        events.append(self._make_event(task, d))
                    d = engine.advance(d, sched)
            elif typ in (TASK_TYPE_SIMPLE, TASK_TYPE_AFTER_COMPLETION):
                if task.get("status") == "done":
                    continue
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
