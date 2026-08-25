# Better ToDo

A feature-rich todo integration for Home Assistant with a custom Lovelace card — built for
recurring tasks that actually work the way you need them to.

> **Status: early development / MVP.** Core features work; expect rough edges.

## Features

- **Two recurrence modes**: schedule-based ("next 1st of the month", regardless of when you
  completed it) and completion-based ("1 month after completion") — the mode most todo apps
  are missing.
- Simple one-off tasks with an optional *visible from* date and a *deadline* (with countdown).
- Weekly/monthly habit-style tasks with streaks ("done 15 weeks in a row") and miss tracking
  ("not done for 3 weeks"). Skipping freezes the streak instead of breaking it.
- Overdue as a **counter** ("3× due") on a single task instead of cluttering the list with
  duplicates — complete one occurrence or all at once.
- Multiple lists, assignment to Home Assistant persons, and **rotating assignment** over a
  configurable pool of persons (e.g. kids rotate taking out the trash).
- Subtasks, optional priorities — features are centrally toggleable in the integration
  options, from "dumb list" to full feature set.
- Services (`better_todo.add_task`, `complete_task`, `skip_task`, `remove_task`) and events
  (`better_todo_item_created/completed/due/overdue`) for automations; completion history.
- A custom dashboard card `better-todo-card` (shipped with the integration, auto-registered
  as a Lovelace resource) with list/person filters, an optional in-card menu, add/edit
  dialogs — following your Home Assistant theme.

## Card

The card is registered automatically. Minimal configuration:

```yaml
type: custom:better-todo-card
```

Options: `title`, `lists` (names/ids, default all), `assigned` (`all` | `me` | person
entity id), `show_menu`, `show_add`, `show_completed`, `show_upcoming`.

## Installation (HACS)

1. In HACS, add this repository as a **custom repository** (category: Integration).
2. Install **Better ToDo** and restart Home Assistant.
3. Add the integration via *Settings → Devices & Services → Add Integration*.

## License

MIT
