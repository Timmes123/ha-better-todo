# Better ToDo

A feature-rich todo integration for Home Assistant with a custom Lovelace card — built for
recurring tasks that actually work the way you need them to.

> **Status: early development.** Not yet functional — this is the project skeleton.

## Planned features

- **Two recurrence modes**: schedule-based ("next 1st of the month", regardless of when you
  completed it) and completion-based ("1 month after completion") — the mode most todo apps
  are missing.
- Simple one-off tasks with an optional *visible from* date and a *deadline* (with countdown).
- Weekly/monthly habit-style tasks with streaks ("done 15 weeks in a row") and miss tracking
  ("not done for 3 weeks").
- Multiple lists, assignment to Home Assistant persons, and **rotating assignment** over a
  configurable pool of persons (e.g. kids rotate taking out the trash).
- Overdue counter instead of cluttering your list with duplicates.
- Subtasks, optional priorities — all features centrally toggleable, from "dumb list" to
  full feature set.
- Services and events for automations, completion history, statistics.
- A dynamic custom dashboard card (shipped with the integration) with filters and an
  optional in-card menu, following your Home Assistant theme.

## Installation (HACS)

1. In HACS, add this repository as a **custom repository** (category: Integration).
2. Install **Better ToDo** and restart Home Assistant.
3. Add the integration via *Settings → Devices & Services → Add Integration*.

## License

MIT
