"""Mirror todo entities: one standard HA todo entity per Better ToDo list.

These make lists usable from the Companion App, watches and voice assistants.
The Better ToDo storage stays the single source of truth.
"""

from __future__ import annotations

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import engine
from .const import DOMAIN, SIGNAL_UPDATE, TASK_TYPE_SIMPLE
from .manager import BetterTodoError, BetterTodoManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: BetterTodoManager = hass.data[DOMAIN]
    known: dict[str, BetterTodoListEntity] = {}

    @callback
    def sync_lists() -> None:
        current = {lst["id"]: lst for lst in manager.data["lists"]}
        added = [
            BetterTodoListEntity(manager, lst)
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


class BetterTodoListEntity(TodoListEntity):
    """A read/write mirror of one Better ToDo list."""

    _attr_should_poll = False
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, manager: BetterTodoManager, lst: dict) -> None:
        self.manager = manager
        self.list_id = lst["id"]
        self._attr_unique_id = f"{DOMAIN}_{lst['id']}_todo"
        self._attr_name = lst["name"]

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
            self._attr_name = lst["name"]
        self.async_write_ha_state()

    @property
    def todo_items(self) -> list[TodoItem]:
        today = dt_util.now().date()
        items: list[TodoItem] = []
        for task in self.manager.data["tasks"]:
            if task["list_id"] != self.list_id:
                continue
            computed = engine.compute_state(task, today)
            state = computed.get("state")
            if state == "hidden":
                continue
            if state == "upcoming" and not computed.get("visible"):
                continue
            done = state in ("done", "period_done")
            items.append(
                TodoItem(
                    uid=task["id"],
                    summary=task["title"],
                    status=TodoItemStatus.COMPLETED if done else TodoItemStatus.NEEDS_ACTION,
                    due=engine.parse_date(computed.get("due")),
                    description=task.get("notes") or None,
                )
            )
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        self.manager.save_task(
            {
                "list_id": self.list_id,
                "title": item.summary or "",
                "type": TASK_TYPE_SIMPLE,
                "notes": item.description or "",
                "due_date": item.due.isoformat() if item.due else None,
            }
        )

    async def async_update_todo_item(self, item: TodoItem) -> None:
        task = next(
            (t for t in self.manager.data["tasks"] if t["id"] == item.uid), None
        )
        if task is None:
            raise BetterTodoError(f"Task {item.uid} not found")
        today = dt_util.now().date()
        state = engine.compute_state(task, today).get("state")
        done = state in ("done", "period_done")
        if item.status == TodoItemStatus.COMPLETED and not done:
            self.manager.complete_task(item.uid, True)
        elif item.status == TodoItemStatus.NEEDS_ACTION and done:
            try:
                self.manager.uncomplete_task(item.uid)
            except BetterTodoError:
                pass  # recurring types cannot be uncompleted
        changes: dict = {"id": item.uid, "list_id": task["list_id"], "title": item.summary or task["title"]}
        if item.description is not None:
            changes["notes"] = item.description
        if item.due is not None and task.get("type") == TASK_TYPE_SIMPLE:
            changes["due_date"] = item.due.isoformat()
        self.manager.save_task(changes)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            self.manager.delete_task(uid)
