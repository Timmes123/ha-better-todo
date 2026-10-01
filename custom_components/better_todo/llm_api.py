"""LLM API: Better ToDo tools for Assist conversation agents.

Registering an API with ``homeassistant.helpers.llm`` makes "Better ToDo"
selectable next to "Assist" in every conversation agent (Anthropic, OpenAI,
Ollama, ...). The tools are built for small local models as much as for
cloud ones: dates are resolved server-side, task titles are matched loosely
with an explicit "ambiguous" answer, every result carries a ready-to-read
``speech`` line in the user's language, and which lists an assistant may
touch is enforced here, not in the prompt.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, llm

from .const import (
    CONF_LLM_AREA_LISTS,
    CONF_LLM_DEFAULT_LIST,
    CONF_LLM_PERSON_LISTS,
    DOMAIN,
    LLM_API_ID,
    LLM_API_NAME,
    MAX_PRIORITY,
    TASK_TYPE_PERIOD,
    TASK_TYPE_SIMPLE,
)
from .manager import BetterTodoError, BetterTodoManager
from .services import (
    SORT_MODES,
    SORT_PRIORITY,
    as_list,
    normalize_fields,
    normalize_tags,
    query_tasks,
)

_LOGGER = logging.getLogger(__name__)

LANGUAGES = ("en", "de", "fr")
CLEAR_WORDS = {"none", "null", "clear", "keine", "kein", "aucun", "aucune", "-"}

WEEKDAYS = {
    "en": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    "de": ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
}
WEEKDAY_SHORT = {
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    "fr": ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"],
}
MONTH_SHORT_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TODAY_WORDS = {"today", "heute", "aujourd'hui", "aujourdhui", "aujourd’hui"}
TOMORROW_WORDS = {"tomorrow", "morgen", "demain"}
DAY_AFTER_WORDS = {
    "day after tomorrow", "the day after tomorrow", "übermorgen", "uebermorgen",
    "après-demain", "apres-demain", "après demain", "apres demain",
}
NEXT_WEEK_WORDS = {
    "next week", "nächste woche", "naechste woche", "la semaine prochaine", "semaine prochaine",
}
NEXT_PREFIXES = ("next ", "nächsten ", "nächste ", "naechsten ", "naechste ", "kommenden ", "am ", "on ")
NEXT_SUFFIXES = (" prochain", " prochaine")

TEXTS: dict[str, dict[str, Any]] = {
    "en": {
        "prio": "priority {n}",
        "prio3": ["high priority", "medium priority", "low priority"],
        "tags": "tags {tags}",
        "overdue_since": "overdue since {date}",
        "times_due": "{n}× due",
        "due_today": "due today",
        "due_tomorrow": "due tomorrow",
        "due_on": "due {date}",
        "at": "at {time}",
        "upcoming": "visible from {date}",
        "this_week": "this week",
        "this_month": "this month",
        "streak": "{n} in a row",
        "for": "for {names}",
        "list": "list {name}",
        "done": "done",
    },
    "de": {
        "prio": "Priorität {n}",
        "prio3": ["hohe Priorität", "mittlere Priorität", "niedrige Priorität"],
        "tags": "Tags {tags}",
        "overdue_since": "überfällig seit {date}",
        "times_due": "{n}× fällig",
        "due_today": "heute fällig",
        "due_tomorrow": "morgen fällig",
        "due_on": "fällig {date}",
        "at": "um {time} Uhr",
        "upcoming": "sichtbar ab {date}",
        "this_week": "diese Woche",
        "this_month": "diesen Monat",
        "streak": "{n} in Folge",
        "for": "für {names}",
        "list": "Liste {name}",
        "done": "erledigt",
    },
    "fr": {
        "prio": "priorité {n}",
        "prio3": ["priorité haute", "priorité moyenne", "priorité basse"],
        "tags": "étiquettes {tags}",
        "overdue_since": "en retard depuis le {date}",
        "times_due": "{n}× à faire",
        "due_today": "à faire aujourd'hui",
        "due_tomorrow": "à faire demain",
        "due_on": "pour {date}",
        "at": "à {time}",
        "upcoming": "visible à partir du {date}",
        "this_week": "cette semaine",
        "this_month": "ce mois-ci",
        "streak": "{n} d'affilée",
        "for": "pour {names}",
        "list": "liste {name}",
        "done": "terminée",
    },
}


# ------------------------------------------------------------------ helpers


def _lang(hass: HomeAssistant, llm_context: llm.LLMContext) -> str:
    """'de', 'fr' or 'en' from the request language, else the HA language."""
    for candidate in (llm_context.language, hass.config.language):
        code = (candidate or "").lower()[:2]
        if code in LANGUAGES:
            return code
    return "en"


def _format_date(d: date, lang: str, today: date) -> str:
    """Short spoken date: weekday + day/month, year only when it differs."""
    weekday = WEEKDAY_SHORT[lang][d.weekday()]
    if lang == "de":
        text = f"{weekday} {d.day:02d}.{d.month:02d}."
        return f"{text}{d.year}" if d.year != today.year else text
    if lang == "fr":
        text = f"{weekday} {d.day:02d}/{d.month:02d}"
        return f"{text}/{d.year}" if d.year != today.year else text
    text = f"{weekday} {d.day} {MONTH_SHORT_EN[d.month - 1]}"
    return f"{text} {d.year}" if d.year != today.year else text


def resolve_date(value: Any, today: date, lang: str = "en") -> date | None:
    """Turn what an assistant passes as a date into a date.

    Accepts YYYY-MM-DD, today/tomorrow/day after tomorrow, next week, a
    weekday name (next occurrence, today included), '+N' or 'N days', in
    English, German and French regardless of ``lang``. Returns None for an
    empty value or a clear word; raises ValueError for anything else so the
    tool can answer with a readable error instead of storing nonsense.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = re.sub(r"\s+", " ", str(value).strip().casefold())
    if not text or text in CLEAR_WORDS:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    if text in TODAY_WORDS:
        return today
    if text in TOMORROW_WORDS:
        return today + timedelta(days=1)
    if text in DAY_AFTER_WORDS:
        return today + timedelta(days=2)
    if text in NEXT_WEEK_WORDS:
        return today + timedelta(days=7)
    if match := re.fullmatch(r"(?:in |\+)?(\d{1,3})\s*(?:d|days?|tage?n?|jours?)?", text):
        return today + timedelta(days=int(match.group(1)))
    if match := re.fullmatch(r"(?:in |\+)?(\d{1,2})\s*(?:w|weeks?|wochen?|semaines?)", text):
        return today + timedelta(weeks=int(match.group(1)))
    explicit_next = False
    for prefix in NEXT_PREFIXES:
        if text.startswith(prefix):
            explicit_next = explicit_next or prefix.strip() not in ("am", "on")
            text = text[len(prefix):].strip()
    for suffix in NEXT_SUFFIXES:
        if text.endswith(suffix):
            explicit_next = True
            text = text[: -len(suffix)].strip()
    for names in WEEKDAYS.values():
        if text in names:
            ahead = (names.index(text) - today.weekday()) % 7
            if ahead == 0 and explicit_next:
                ahead = 7
            return today + timedelta(days=ahead)
    raise ValueError(value)


def _norm(text: str) -> str:
    text = re.sub(r"[^\w\s]", " ", (text or "").casefold())
    return re.sub(r"\s+", " ", text).strip()


def match_tasks(pool: list[dict], query: str) -> tuple[dict | None, list[dict]]:
    """Find the task an assistant means.

    Returns ``(task, [])`` for a unique hit, ``(None, candidates)`` when
    several tasks fit or only part of the query fits, and ``(None, [])`` when
    nothing does. An exact title wins over a substring ('milk' must not pick
    'coconut milk' when both exist), then a substring in either direction,
    then all words of the query; a partial word match is never acted on.
    """
    query = (query or "").strip()
    if not query:
        return None, []
    for task in pool:
        if task["id"] == query:
            return task, []
    q = _norm(query)
    if not q:
        return None, []
    exact = [t for t in pool if _norm(t["title"]) == q]
    if len(exact) == 1:
        return exact[0], []
    if exact:
        return None, exact
    substring = [t for t in pool if q in _norm(t["title"]) or _norm(t["title"]) in q]
    if len(substring) == 1:
        return substring[0], []
    if substring:
        return None, substring
    words = q.split()
    by_words = [t for t in pool if all(w in _norm(t["title"]) for w in words)]
    if len(by_words) == 1:
        return by_words[0], []
    if by_words:
        return None, by_words
    # "I called the plumber" vs "Call plumber Dupont": only some words fit
    # (inflection, filler words). Never act on that alone — hand the
    # candidates back so the agent confirms with the user.
    strong = [w for w in words if len(w) >= 4]
    if strong:
        partial = [t for t in pool if any(w in _norm(t["title"]) for w in strong)]
        return None, partial[:5]
    return None, []


# -------------------------------------------------------------------- scope


@dataclass(slots=True)
class Scope:
    """Which lists one request may use, and who is asking."""

    lists: list[dict]  # allowed lists in display order
    default: dict | None  # list for new tasks without an explicit list
    restricted: bool  # a person/area rule applied
    person: dict | None  # the calling person, when the request carries a user
    area_id: str | None

    @property
    def list_ids(self) -> set[str]:
        return {lst["id"] for lst in self.lists}

    def list_by_name(self, name: str) -> dict | None:
        key = (name or "").strip().casefold()
        return next((lst for lst in self.lists if lst["name"].casefold() == key), None)


def _person_for_user(hass: HomeAssistant, user_id: str | None) -> dict | None:
    if not user_id:
        return None
    for state in hass.states.async_all("person"):
        if state.attributes.get("user_id") == user_id:
            return {"entity_id": state.entity_id, "name": state.name or state.entity_id}
    return None


def _area_for_device(hass: HomeAssistant, device_id: str | None) -> str | None:
    if not device_id:
        return None
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return None
    effective = getattr(dr, "async_get_effective_area_id", None)
    if effective is not None:
        return effective(hass, device)
    return device.area_id


@callback
def resolve_scope(
    hass: HomeAssistant, manager: BetterTodoManager, llm_context: llm.LLMContext
) -> Scope:
    options = manager.entry.options or {}
    lists = sorted(manager.data["lists"], key=lambda l: l.get("order", 0))
    by_id = {lst["id"]: lst for lst in lists}
    person = _person_for_user(
        hass, llm_context.context.user_id if llm_context.context else None
    )
    area_id = _area_for_device(hass, llm_context.device_id)

    allowed_ids: list[str] | None = None
    person_rules = options.get(CONF_LLM_PERSON_LISTS) or {}
    area_rules = options.get(CONF_LLM_AREA_LISTS) or {}
    if person and person_rules.get(person["entity_id"]):
        allowed_ids = list(person_rules[person["entity_id"]])
    elif area_id and area_rules.get(area_id):
        allowed_ids = list(area_rules[area_id])

    if allowed_ids is None:
        allowed = lists
    else:
        allowed = [lst for lst in lists if lst["id"] in set(allowed_ids)]
    default_id = options.get(CONF_LLM_DEFAULT_LIST)
    default = by_id.get(default_id) if default_id in {l["id"] for l in allowed} else None
    if default is None and allowed:
        default = allowed[0]
    return Scope(
        lists=allowed,
        default=default,
        restricted=allowed_ids is not None,
        person=person,
        area_id=area_id,
    )


# ------------------------------------------------------------------ results


def _tool_result(data: dict, error: bool = False):
    """ToolResult on HA 2026.10+, a plain dict before that."""
    result_cls = getattr(llm, "ToolResult", None)
    if result_cls is not None:
        return result_cls(data=data, error=error)
    return data


def _error(message: str, **extra) -> Any:
    return _tool_result({"success": False, "error": message, **extra}, error=True)


def _speech(row: dict, lang: str, today: date, levels: int, name_list: bool) -> str:
    t = TEXTS[lang]
    details: list[str] = []
    prio = row.get("priority")
    if prio is not None:
        if levels == 3 and 1 <= prio <= 3:
            details.append(t["prio3"][prio - 1])
        else:
            details.append(t["prio"].format(n=prio))
    state = row.get("state")
    due = row.get("due")
    due_date = date.fromisoformat(due) if due else None
    if row.get("done"):
        details.append(t["done"])
    elif row.get("type") == TASK_TYPE_PERIOD:
        details.append(t["this_week"] if row.get("period") == "week" else t["this_month"])
        if row.get("streak"):
            details.append(t["streak"].format(n=row["streak"]))
    elif state == "overdue" and due_date:
        details.append(t["overdue_since"].format(date=_format_date(due_date, lang, today)))
        if (row.get("due_count") or 1) > 1:
            details.append(t["times_due"].format(n=row["due_count"]))
    elif state == "due":
        details.append(t["due_today"])
    elif state == "hidden" and row.get("visible_from"):
        details.append(
            t["upcoming"].format(date=_format_date(date.fromisoformat(row["visible_from"]), lang, today))
        )
    elif due_date:
        if due_date == today + timedelta(days=1):
            details.append(t["due_tomorrow"])
        else:
            details.append(t["due_on"].format(date=_format_date(due_date, lang, today)))
    if row.get("due_time") and not row.get("done"):
        details.append(t["at"].format(time=row["due_time"]))
    if row.get("tags"):
        details.append(t["tags"].format(tags=", ".join(row["tags"])))
    if row.get("assigned_names"):
        details.append(t["for"].format(names=", ".join(row["assigned_names"])))
    if name_list and row.get("list"):
        details.append(t["list"].format(name=row["list"]))
    return f"{row['title']} ({', '.join(details)})" if details else row["title"]


def _row(task_row: dict, lang: str, today: date, levels: int, name_list: bool) -> dict:
    """A get_tasks row trimmed for an LLM, plus the speech line."""
    row = {
        "task_id": task_row["task_id"],
        "title": task_row["title"],
        "list": task_row["list"],
        "state": task_row["state"],
        "due": task_row.get("due"),
        "due_time": task_row.get("due_time"),
        "priority": task_row.get("priority"),
        "tags": task_row.get("tags") or [],
        "assigned_to": task_row.get("assigned_names") or [],
    }
    if task_row.get("notes"):
        row["notes"] = task_row["notes"]
    if task_row.get("due_count") and task_row["due_count"] > 1:
        row["due_count"] = task_row["due_count"]
    subtasks = task_row.get("subtasks") or []
    if subtasks:
        row["subtasks_open"] = [s["title"] for s in subtasks if not s["done"]]
    row["speech"] = _speech(task_row, lang, today, levels, name_list)
    return row


# -------------------------------------------------------------------- tools


class _BetterTodoTool(llm.Tool):
    """Base: tags the tool with the integration and its behaviour."""

    integration = DOMAIN
    read_only = False
    destructive = False
    idempotent = False

    def __init__(self) -> None:
        annotations_cls = getattr(llm, "ToolAnnotations", None)
        if annotations_cls is not None:
            self.annotations = annotations_cls(
                read_only=self.read_only,
                destructive=self.destructive,
                idempotent=self.idempotent,
                open_world=False,
            )

    async def async_call(
        self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext
    ):
        manager: BetterTodoManager | None = hass.data.get(DOMAIN)
        if manager is None:
            return _error("Better ToDo is not loaded")
        ctx = _CallContext(hass, manager, llm_context)
        try:
            return self.handle(ctx, dict(tool_input.tool_args))
        except BetterTodoError as err:
            return _error(str(err))
        except (ValueError, TypeError, KeyError) as err:
            _LOGGER.debug("LLM tool %s failed: %s", self.name, err)
            return _error(f"Invalid input: {err}")

    def handle(self, ctx: _CallContext, args: dict) -> Any:
        raise NotImplementedError


class _CallContext:
    """Everything one tool call needs: scope, language, caller."""

    def __init__(self, hass: HomeAssistant, manager: BetterTodoManager, llm_context: llm.LLMContext) -> None:
        self.hass = hass
        self.manager = manager
        self.llm_context = llm_context
        self.scope = resolve_scope(hass, manager, llm_context)
        self.lang = _lang(hass, llm_context)
        self.today = manager._today()
        self.levels = manager.priority_levels
        self.name_list = len(self.scope.lists) > 1

    @property
    def by(self) -> str:
        if self.scope.person:
            return self.scope.person["name"]
        return "Assist"

    def require_lists(self) -> None:
        if not self.scope.lists:
            raise BetterTodoError(
                "No task lists are available to this assistant. Check the "
                "Better ToDo options (Voice assistants)."
            )

    def available_lists(self) -> str:
        return ", ".join(lst["name"] for lst in self.scope.lists) or "-"

    def list_for(self, name: str | None, *, required_default: bool = True) -> dict | None:
        """The list an assistant named, within the scope; None for no name."""
        self.require_lists()
        if not (name or "").strip():
            return self.scope.default if required_default else None
        lst = self.scope.list_by_name(name)
        if lst is None:
            raise BetterTodoError(
                f"List '{name}' is not available here. Available lists: {self.available_lists()}."
            )
        return lst

    def list_filter(self, names: Any) -> list[str] | None:
        """List names for query_tasks: what was asked (validated), else the scope."""
        self.require_lists()
        wanted = as_list(names)
        if wanted:
            return [self.list_for(n)["name"] for n in wanted]
        return [lst["name"] for lst in self.scope.lists] if self.scope.restricted else None

    def persons(self, values: Any) -> list[str] | None:
        """Person entity ids for names/entity ids; 'me' is the caller."""
        wanted = as_list(values)
        if not wanted:
            return None
        if any(v.casefold() in CLEAR_WORDS for v in wanted):
            return []
        persons = self.manager.serialized_data()["persons"]
        ids: list[str] = []
        for value in wanted:
            key = value.casefold()
            if key in ("me", "ich", "moi", "myself", "mir", "mich"):
                if not self.scope.person:
                    raise BetterTodoError("Who is asking is unknown; name the person.")
                ids.append(self.scope.person["entity_id"])
                continue
            match = next(
                (
                    p for p in persons
                    if p["entity_id"].casefold() == key or (p["name"] or "").casefold() == key
                ),
                None,
            )
            if match is None:
                names = ", ".join(p["name"] or p["entity_id"] for p in persons) or "-"
                raise BetterTodoError(f"Unknown person '{value}'. Known persons: {names}.")
            if match["entity_id"] not in ids:
                ids.append(match["entity_id"])
        return ids

    def date(self, value: Any, field: str = "due") -> str | None:
        try:
            resolved = resolve_date(value, self.today)
        except ValueError as err:
            weekday = WEEKDAYS["en"][self.today.weekday()].capitalize()
            raise BetterTodoError(
                f"Unknown {field} '{value}'. Use YYYY-MM-DD, today, tomorrow, a weekday "
                f"name or +N days. Today is {weekday} {self.today.isoformat()}."
            ) from err
        return resolved.isoformat() if resolved else None

    def priority(self, value: Any) -> int | None:
        if value is None or (isinstance(value, str) and value.strip().casefold() in CLEAR_WORDS | {""}):
            return None
        try:
            prio = int(value)
        except (ValueError, TypeError) as err:
            raise BetterTodoError(f"Priority must be a number from 1 to {self.levels}.") from err
        if prio == 0:
            return None
        if not 1 <= prio <= MAX_PRIORITY:
            raise BetterTodoError(f"Priority must be a number from 1 to {self.levels} (1 = highest).")
        return prio

    def rows(self, filters: dict) -> list[dict]:
        data = {k: v for k, v in filters.items() if v not in (None, "")}
        data["list"] = self.list_filter(data.get("list"))
        if data["list"] is None:
            del data["list"]
        if "assigned_to" in data:
            data["assigned_to"] = self.persons(data["assigned_to"])
        data.setdefault("sort", SORT_PRIORITY)
        result = query_tasks(self.manager, data)
        # Naming the list on every line is noise when one list was asked for.
        name_list = self.name_list and len(data.get("list") or []) != 1
        return [
            _row(r, self.lang, self.today, self.levels, name_list)
            for r in result["tasks"]
        ]

    def row_for(self, task_id: str) -> dict:
        rows = query_tasks(self.manager, {"status": "all"})["tasks"]
        row = next(r for r in rows if r["task_id"] == task_id)
        return _row(row, self.lang, self.today, self.levels, self.name_list)

    def find(self, query: str, list_name: str | None) -> dict:
        """The stored task meant by ``query`` within the scope, or raise
        ``_Ambiguous`` / ``BetterTodoError`` with candidates."""
        self.require_lists()
        lst = self.list_for(list_name, required_default=False)
        allowed = {lst["id"]} if lst else self.scope.list_ids
        pool = []
        for task in self.manager.data["tasks"]:
            if task["list_id"] not in allowed:
                continue
            state = self.manager.computed_state(task, self.today).get("state")
            if state in ("done", "period_done", "error"):
                continue
            pool.append(task)
        task, candidates = match_tasks(pool, query)
        if task is not None:
            return task
        if candidates:
            raise _Ambiguous(query, [self.row_for(c["id"]) for c in candidates])
        raise BetterTodoError(
            f"No open task matches '{query}'. Use list_tasks to see the open tasks."
        )


class _Ambiguous(Exception):
    def __init__(self, query: str, candidates: list[dict]) -> None:
        super().__init__(query)
        self.query = query
        self.candidates = candidates


def _ambiguous_result(err: _Ambiguous) -> Any:
    return _tool_result(
        {
            "success": False,
            "error": "ambiguous",
            "message": (
                f"No unique match for '{err.query}'. Ask the user which of the "
                "candidates they mean (or whether they mean the one candidate) and "
                "call again with its exact title or task_id."
            ),
            "candidates": err.candidates,
        },
        error=True,
    )


class ListTasksTool(_BetterTodoTool):
    name = "list_tasks"
    title = "List tasks"
    description = (
        "Read tasks from the Better ToDo lists. Returns the matching tasks sorted by "
        "importance (priority, then due date) with a ready-to-read 'speech' line per "
        "task. All filters are optional; without filters all open tasks of the lists "
        "available here are returned."
    )
    parameters = vol.Schema(
        {
            vol.Optional("list", description="Only tasks of this list (name)."): str,
            vol.Optional(
                "assigned_to",
                description="Only tasks assigned to this person (name, or 'me' for the current user).",
            ): str,
            vol.Optional("tags", description="Only tasks with one of these tags (comma-separated)."): str,
            vol.Optional(
                "due",
                description="today = due today or overdue, overdue = overdue only, week = due within 7 days.",
            ): vol.In(["today", "overdue", "week"]),
            vol.Optional(
                "priority",
                description="Only tasks with this priority or more important (1 = most important).",
            ): vol.Coerce(int),
            vol.Optional("status", description="open (default), done or all."): vol.In(["open", "done", "all"]),
            vol.Optional(
                "sort", description="priority (default) or due (earliest due date first)."
            ): vol.In(SORT_MODES),
        }
    )
    read_only = True
    idempotent = True

    def handle(self, ctx: _CallContext, args: dict) -> Any:
        rows = ctx.rows(
            {
                "list": args.get("list"),
                "assigned_to": args.get("assigned_to"),
                "tags": args.get("tags"),
                "due": args.get("due"),
                "priority": ctx.priority(args.get("priority")),
                "status": args.get("status") or "open",
                "sort": args.get("sort") or SORT_PRIORITY,
                "include_unassigned": False if args.get("assigned_to") else True,
            }
        )
        return _tool_result({"success": True, "count": len(rows), "tasks": rows})


class AddTaskTool(_BetterTodoTool):
    name = "add_task"
    title = "Add task"
    description = (
        "Add a new task to a Better ToDo list. Only the title is required; the list "
        "defaults to the list configured for this assistant. Never guess a date: pass "
        "it as YYYY-MM-DD, today, tomorrow, a weekday name or +N (days), or leave it out."
    )
    parameters = vol.Schema(
        {
            vol.Required("title", description="Short task title, as the user would read it."): str,
            vol.Optional("list", description="List name. Omit for the default list."): str,
            vol.Optional(
                "due",
                description="Due date: YYYY-MM-DD, today, tomorrow, a weekday name or +N days.",
            ): str,
            vol.Optional("due_time", description="Due time HH:MM (24h)."): str,
            vol.Optional(
                "priority",
                description="1 = most important. Omit when the user did not mention importance.",
            ): vol.Coerce(int),
            vol.Optional("tags", description="Tags, comma-separated, without '#'."): str,
            vol.Optional(
                "assigned_to",
                description="Person responsible (name, or 'me' for the current user).",
            ): str,
            vol.Optional("notes", description="Additional details."): str,
        }
    )

    def handle(self, ctx: _CallContext, args: dict) -> Any:
        lst = ctx.list_for(args.get("list"))
        title = (args.get("title") or "").strip()
        if not title:
            raise BetterTodoError("A task title is required.")
        task = {
            "list_id": lst["id"],
            "title": title,
            "type": TASK_TYPE_SIMPLE,
            "due_date": ctx.date(args.get("due")),
            "priority": ctx.priority(args.get("priority")),
            "tags": normalize_tags(args.get("tags")),
            "notes": (args.get("notes") or "").strip() or None,
        }
        if args.get("due_time"):
            if not task["due_date"]:
                task["due_date"] = ctx.today.isoformat()
            task["due_time"] = args["due_time"]
        persons = ctx.persons(args.get("assigned_to"))
        if persons:
            task["assigned_to"] = persons
        normalize_fields(task)
        saved = ctx.manager.save_task(task)
        row = ctx.row_for(saved["id"])
        return _tool_result({"success": True, "task": row})


class CompleteTaskTool(_BetterTodoTool):
    name = "complete_task"
    title = "Complete task"
    description = (
        "Mark a task as done. Pass what the user said as 'task'; titles are matched "
        "loosely. If the answer is 'ambiguous', ask the user which of the candidates "
        "they mean and call again with its exact title or task_id."
    )
    parameters = vol.Schema(
        {
            vol.Required("task", description="Task title (or part of it) or task_id."): str,
            vol.Optional("list", description="List name to narrow the search."): str,
            vol.Optional(
                "all",
                description="For a recurring task that is due several times: complete all pending occurrences.",
            ): bool,
        }
    )
    idempotent = True

    def handle(self, ctx: _CallContext, args: dict) -> Any:
        try:
            task = ctx.find(args.get("task") or "", args.get("list"))
        except _Ambiguous as err:
            return _ambiguous_result(err)
        ctx.manager.complete_task(task["id"], bool(args.get("all")), ctx.by)
        return _tool_result({"success": True, "task": ctx.row_for(task["id"])})


class SkipTaskTool(_BetterTodoTool):
    name = "skip_task"
    title = "Skip task"
    description = (
        "Skip the current occurrence of a recurring or weekly/monthly task without "
        "completing it (streaks are kept). Titles are matched loosely like complete_task."
    )
    parameters = vol.Schema(
        {
            vol.Required("task", description="Task title (or part of it) or task_id."): str,
            vol.Optional("list", description="List name to narrow the search."): str,
        }
    )
    idempotent = True

    def handle(self, ctx: _CallContext, args: dict) -> Any:
        try:
            task = ctx.find(args.get("task") or "", args.get("list"))
        except _Ambiguous as err:
            return _ambiguous_result(err)
        ctx.manager.skip_task(task["id"], ctx.by)
        return _tool_result({"success": True, "task": ctx.row_for(task["id"])})


class UpdateTaskTool(_BetterTodoTool):
    name = "update_task"
    title = "Update task"
    description = (
        "Change an existing task: due date, time, priority, tags, person, title, "
        "notes or list. Only the fields passed are changed. Titles are matched "
        "loosely like complete_task."
    )
    parameters = vol.Schema(
        {
            vol.Required("task", description="Current task title (or part of it) or task_id."): str,
            vol.Optional("list", description="List name to narrow the search."): str,
            vol.Optional("new_title", description="New title."): str,
            vol.Optional(
                "due",
                description="New due date (YYYY-MM-DD, today, tomorrow, weekday, +N days) or 'none' to clear.",
            ): str,
            vol.Optional("due_time", description="New due time HH:MM, or 'none' to clear."): str,
            vol.Optional("priority", description="New priority (1 = most important), 0 to clear."): vol.Coerce(int),
            vol.Optional("tags", description="New tags, comma-separated (replaces the old ones)."): str,
            vol.Optional(
                "assigned_to",
                description="New responsible person (name or 'me'), or 'none' to unassign.",
            ): str,
            vol.Optional("notes", description="New notes."): str,
            vol.Optional("move_to_list", description="Move the task to this list."): str,
        }
    )
    idempotent = True

    def handle(self, ctx: _CallContext, args: dict) -> Any:
        try:
            task = ctx.find(args.get("task") or "", args.get("list"))
        except _Ambiguous as err:
            return _ambiguous_result(err)
        data = dict(task)
        if (new_title := (args.get("new_title") or "").strip()):
            data["title"] = new_title
        if args.get("move_to_list"):
            data["list_id"] = ctx.list_for(args["move_to_list"])["id"]
        if "due" in args:
            due = ctx.date(args["due"])
            if due is None and task.get("type") != TASK_TYPE_SIMPLE:
                raise BetterTodoError("A recurring task needs a due date; set a new one instead.")
            data["due_date"] = due
        if "due_time" in args:
            value = (args.get("due_time") or "").strip()
            data["due_time"] = None if value.casefold() in CLEAR_WORDS | {""} else value
            if data["due_time"] and not data.get("due_date"):
                data["due_date"] = ctx.today.isoformat()
        if "priority" in args:
            data["priority"] = ctx.priority(args["priority"])
        if "tags" in args:
            data["tags"] = normalize_tags(args["tags"])
        if "assigned_to" in args:
            data["assigned_to"] = ctx.persons(args["assigned_to"]) or []
            if data["assigned_to"] and task.get("rotation"):
                data["rotation"] = None
        if "notes" in args:
            data["notes"] = (args.get("notes") or "").strip() or None
        ctx.manager.save_task(data)
        return _tool_result({"success": True, "task": ctx.row_for(task["id"])})


TOOLS = (ListTasksTool, AddTaskTool, CompleteTaskTool, SkipTaskTool, UpdateTaskTool)


# ---------------------------------------------------------------------- API


class BetterTodoAPI(llm.API):
    """The Better ToDo tool set, one instance per request."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass=hass, id=LLM_API_ID, name=LLM_API_NAME)

    async def async_get_api_instance(self, llm_context: llm.LLMContext) -> llm.APIInstance:
        manager: BetterTodoManager | None = self.hass.data.get(DOMAIN)
        tools: list[llm.Tool] = [cls() for cls in TOOLS]
        return llm.APIInstance(
            api=self,
            api_prompt=self._prompt(manager, llm_context),
            llm_context=llm_context,
            tools=tools,
        )

    def _prompt(self, manager: BetterTodoManager | None, llm_context: llm.LLMContext) -> str:
        if manager is None:
            return "Better ToDo is not loaded."
        scope = resolve_scope(self.hass, manager, llm_context)
        today = manager._today()
        levels = manager.priority_levels
        lines = [
            "Better ToDo keeps the household's task lists. Use its tools for anything "
            "about tasks, chores, todos or shopping items.",
            f"Today is {WEEKDAYS['en'][today.weekday()].capitalize()} {today.isoformat()}.",
        ]
        if scope.lists:
            names = []
            for lst in scope.lists:
                mark = " (default for new tasks)" if scope.default and lst["id"] == scope.default["id"] else ""
                names.append(f"{lst['name']}{mark}")
            lines.append("Lists available here: " + "; ".join(names) + ".")
        else:
            lines.append("No lists are available to this assistant.")
        persons = manager.serialized_data()["persons"]
        if persons:
            lines.append("Persons: " + ", ".join(p["name"] or p["entity_id"] for p in persons) + ".")
        if scope.person:
            lines.append(f"The user talking to you is {scope.person['name']}.")
        if levels == 3:
            lines.append("Priorities: 1 = high, 2 = medium, 3 = low.")
        else:
            lines.append(f"Priorities: 1 (most important) to {levels}.")
        lines.append(
            "Rules: use these tools for everything about tasks and lists, not the generic "
            "to-do list tools. Answer in the user's language and read the 'speech' field "
            "of a task when you mention it. Set a priority, date or person only when the "
            "user says so. Pass dates exactly as said (today, tomorrow, a weekday, "
            "YYYY-MM-DD) and never compute them yourself; the tools resolve them. Several "
            "items in one sentence are one add_task call per item. A spoken category "
            "('house', 'kids') is a tag, not a list; only use a list the user names. If a "
            "tool returns an error or 'ambiguous', tell the user and ask instead of "
            "claiming success. Tags are plain words without '#'."
        )
        return "\n".join(lines)


@callback
def async_register_llm_api(hass: HomeAssistant):
    """Register the API; returns the unregister callback."""
    return llm.async_register_api(hass, BetterTodoAPI(hass))
