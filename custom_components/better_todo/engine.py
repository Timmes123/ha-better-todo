"""Pure date logic for Better ToDo: recurrence, overdue counting, periods.

Everything here works on plain dicts and datetime.date objects and has no
Home Assistant dependencies, so it can be tested standalone.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

MAX_ITER = 1000


def parse_date(value: str | date | None) -> date | None:
    """Parse an ISO date string into a date."""
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value[:10])


def add_months(d: date, months: int, day: int | None = None) -> date:
    """Add months to a date, clamping the day to the month's length.

    ``day`` preserves the intended day-of-month (e.g. 31) across shorter
    months; without it the source date's day is used.
    """
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    dom = day if day else d.day
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(dom, last))


def nth_weekday_of_month(year: int, month: int, nth: int, weekday: int) -> date:
    """Date of the nth (1-4, or -1 = last) given weekday in a month."""
    if nth == -1:
        last = date(year, month, calendar.monthrange(year, month)[1])
        return last - timedelta(days=(last.weekday() - weekday) % 7)
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + (nth - 1) * 7)


def _monthly_date(year: int, month: int, sched: dict, fallback_day: int) -> date:
    """Resolve the concrete date within a month for a monthly/yearly rule."""
    nth = sched.get("nth")
    if nth and nth.get("weekday") is not None:
        return nth_weekday_of_month(year, month, int(nth.get("n") or 1), int(nth["weekday"]))
    day = sched.get("day")
    last = calendar.monthrange(year, month)[1]
    if day == "last":
        return date(year, month, last)
    return date(year, month, min(int(day or fallback_day), last))


def advance(anchor: date, sched: dict) -> date:
    """Return the occurrence following ``anchor`` for a schedule."""
    freq = sched.get("freq", "monthly")
    interval = max(1, int(sched.get("interval") or 1))
    if freq == "daily":
        return anchor + timedelta(days=interval)
    if freq == "weekly":
        weekdays = sorted({int(w) for w in (sched.get("weekdays") or [])})
        if not weekdays:
            return anchor + timedelta(weeks=interval)
        for wd in weekdays:
            if wd > anchor.weekday():
                return anchor + timedelta(days=wd - anchor.weekday())
        # Wrap to the first selected weekday, `interval` week-blocks ahead.
        days_to_monday = 7 * interval - anchor.weekday()
        return anchor + timedelta(days=days_to_monday + weekdays[0])
    if freq == "monthly":
        months = anchor.year * 12 + (anchor.month - 1) + interval
        return _monthly_date(months // 12, months % 12 + 1, sched, anchor.day)
    if freq == "yearly":
        return _monthly_date(anchor.year + interval, anchor.month, sched, anchor.day)
    raise ValueError(f"Unknown schedule frequency: {freq}")


def due_info(anchor: date, sched: dict, today: date) -> tuple[int, date]:
    """Count occurrences due up to today and return the next future one.

    ``anchor`` is the earliest unhandled occurrence. Returns
    ``(due_count, next_future_occurrence)``.
    """
    until = parse_date(sched.get("until"))
    count = 0
    d = anchor
    while d <= today and count < MAX_ITER and (until is None or d <= until):
        count += 1
        d = advance(d, sched)
    return count, d


def schedule_ended(task: dict, new_anchor: date) -> bool:
    """True when a scheduled task has no further occurrences."""
    sched = task.get("schedule") or {}
    until = parse_date(sched.get("until"))
    if until and new_anchor > until:
        return True
    max_occ = sched.get("max_occurrences")
    if max_occ and int(task.get("occurrence_count") or 0) >= int(max_occ):
        return True
    return False


def complete_anchor(anchor: date, sched: dict, today: date, complete_all: bool) -> date:
    """Return the new anchor after completing one or all due occurrences."""
    count, _next_future = due_info(anchor, sched, today)
    if count == 0 or not complete_all:
        # Completing early, or checking off exactly one due occurrence.
        return advance(anchor, sched)
    d = anchor
    while d <= today:
        d = advance(d, sched)
    return d


def add_interval(start: date, interval: dict) -> date:
    """Apply an after-completion interval to a date."""
    unit = interval.get("unit", "days")
    value = max(1, int(interval.get("value") or 1))
    if unit == "days":
        return start + timedelta(days=value)
    if unit == "weeks":
        return start + timedelta(weeks=value)
    if unit == "months":
        return add_months(start, value)
    raise ValueError(f"Unknown interval unit: {unit}")


def period_start(period: str, d: date) -> date:
    """Return the first day of the week/month period containing ``d``."""
    if period == "week":
        return d - timedelta(days=d.weekday())
    return d.replace(day=1)


def next_period(period: str, start: date) -> date:
    if period == "week":
        return start + timedelta(weeks=1)
    return add_months(start, 1, 1)


def rollover(task: dict, today: date) -> bool:
    """Advance a period task into the current period, updating streak/misses.

    A period that ended without completion resets the streak and counts a
    miss; a skipped period freezes the streak and does not count as a miss.
    Returns True if the task changed.
    """
    period = task.get("period") or "week"
    current = period_start(period, today)
    stored = parse_date(task.get("period_start")) or current
    changed = False
    guard = 0
    while stored < current and guard < MAX_ITER:
        done = bool(task.get("period_done"))
        skipped = bool(task.get("period_skipped"))
        if not done and not skipped:
            task["misses"] = int(task.get("misses") or 0) + 1
            task["streak"] = 0
        task["period_done"] = False
        task["period_skipped"] = False
        stored = next_period(period, stored)
        changed = True
        guard += 1
    if task.get("period_start") != stored.isoformat():
        task["period_start"] = stored.isoformat()
        changed = True
    return changed


def compute_state(task: dict, today: date) -> dict:
    """Compute the display state of a task for a given day."""
    typ = task.get("type", "simple")
    if task.get("ended"):
        return {"state": "done"}

    if typ == "simple":
        if task.get("status") == "done":
            return {"state": "done"}
        visible_from = parse_date(task.get("visible_from"))
        if visible_from and visible_from > today:
            return {"state": "hidden", "visible_from": visible_from.isoformat()}
        due = parse_date(task.get("due_date"))
        if due:
            days_left = (due - today).days
            if days_left < 0:
                return {"state": "overdue", "days_overdue": -days_left, "due": due.isoformat()}
            if days_left == 0:
                return {"state": "due", "due": due.isoformat(), "days_overdue": 0}
            return {"state": "open", "days_left": days_left, "due": due.isoformat()}
        return {"state": "open"}

    if typ == "scheduled":
        anchor = parse_date(task.get("due_date")) or today
        count, next_future = due_info(anchor, task.get("schedule") or {}, today)
        if count == 0:
            days_until = (anchor - today).days
            lead = task.get("lead_days")
            return {
                "state": "upcoming",
                "due": anchor.isoformat(),
                "days_until": days_until,
                "visible": lead is not None and days_until <= int(lead),
            }
        days_overdue = (today - anchor).days
        return {
            "state": "due" if days_overdue == 0 else "overdue",
            "due": anchor.isoformat(),
            "due_count": count,
            "days_overdue": days_overdue,
            "next": next_future.isoformat(),
        }

    if typ == "after_completion":
        due = parse_date(task.get("due_date")) or today
        days_until = (due - today).days
        if days_until > 0:
            lead = task.get("lead_days")
            return {
                "state": "upcoming",
                "due": due.isoformat(),
                "days_until": days_until,
                "visible": lead is not None and days_until <= int(lead),
            }
        return {
            "state": "due" if days_until == 0 else "overdue",
            "due": due.isoformat(),
            "due_count": 1,
            "days_overdue": -days_until,
        }

    # period task
    if task.get("period_done"):
        state = "period_done"
    elif task.get("period_skipped"):
        state = "period_skipped"
    else:
        state = "period_open"
    return {
        "state": state,
        "streak": int(task.get("streak") or 0),
        "misses": int(task.get("misses") or 0),
        "period": task.get("period", "week"),
    }
