<p align="center">
  <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/branding/icon.png" width="110" alt="Better ToDo logo">
</p>

# Better ToDo

[![GitHub release](https://img.shields.io/github/v/release/Timmes123/ha-better-todo)](https://github.com/Timmes123/ha-better-todo/releases)
[![Validate](https://github.com/Timmes123/ha-better-todo/actions/workflows/validate.yml/badge.svg)](https://github.com/Timmes123/ha-better-todo/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](https://github.com/Timmes123/ha-better-todo/blob/main/LICENSE)
[![Community Forum](https://img.shields.io/badge/community-forum-41BDF5.svg?logo=homeassistant&logoColor=white)](https://community.home-assistant.io/t/better-todo-flexible-recurring-tasks-habits-household-rotation-for-ha/1022821)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-donate-FF5E5B?logo=kofi&logoColor=white)](https://ko-fi.com/timmes123)
[![PayPal](https://img.shields.io/badge/PayPal-donate-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/timmes123)

A task manager for Home Assistant with a custom dashboard card — built for
**recurring tasks that actually work the way you need them to**.

<p align="center">
  <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/images/card-overview.png" width="400" alt="Better ToDo card overview">
</p>

## Why another todo integration?

Most todo apps (including the built-in HA todo lists) only support one kind of recurrence:
a fixed schedule. Real life needs more:

| Use case | What Better ToDo does |
|---|---|
| 💸 *"Pay the bill — due on the 1st of every month."* You pay it on the 10th. | The next occurrence is still the **1st of the next month** (schedule-based recurrence). Missed months don't pile up as duplicates — you get a single task with a **"3× due" counter** and can complete one occurrence or all at once. |
| 🚽 *"Deep-clean the bathroom — once a month."* You do it 3 weeks late. | The next occurrence is **one month after you actually did it** (after-completion recurrence) — no nagging about a stale schedule. |
| 📄 *"Cancel the contract before Dec 31."* | The task stays invisible until Dec 1 (**visible-from date**), then shows a **live countdown** to the deadline. |
| 🚴 *"Ride the bike once a week."* | A **weekly task** that reopens every Monday, tracks your **streak** ("15 wk streak 🔥") and how long you've been skipping it ("3 wk missed"). Skipping deliberately **freezes** the streak instead of breaking it. |
| 🗑️ *"Kids take turns carrying out the trash."* | **Rotating assignment** over a freely chosen pool of persons — every completion passes the task to the next person. |

## Features

- **Four task types**: one-time (with optional visible-from + deadline countdown),
  recurring on a fixed schedule, recurring after completion, and weekly/monthly
  habit-style tasks with streaks.
- **Cron-style schedules**: every N days/weeks/months/years, multiple weekdays per week,
  a fixed day of month (1–31), the *last* day of the month, the *nth* or *last* weekday
  ("2nd Saturday", "last Wednesday"), yearly on a fixed date — plus an optional end date
  or maximum number of repetitions. The repeat badge on every task shows its cadence
  ("weekly", "every 2 weeks", "2 wk after completion").
- **Notifications out of the box**: per-task reminders (up to 5) and a daily summary of
  open tasks are **pushed by the integration itself** — configure once, no automations
  needed. See [Notifications](#notifications) for the exact mechanics.
- **Assign tasks to one or more persons** (HA `person` entities). Everyone assigned sees
  the task in their personal view; completing it completes it for all. Or check
  **Rotate** and the task belongs to exactly one person at a time, moving on after every
  completion. A "logged-in user" filter gives every family member their own view without
  per-user dashboards.
- **Multiple lists** with in-card management (create, rename, delete), **tags** with
  filter chips and a tap-to-reuse tag picker, subtasks, optional priorities.
- **Standard `todo` entity and `calendar` entity per list** — your tasks show up in the
  Companion App, on watches, in voice assistants and in the HA calendar (recurring tasks
  are expanded onto every occurrence). Better ToDo's own storage stays the single source
  of truth; deleting a list cleans up its entities.
- **Services and events** for automations, plus a completion history from day one.
- **Feature toggles**: switch off everything you don't need (priorities, subtasks,
  assignment, rotation, habit tasks, tags, mirror/calendar entities) — from "dumb list"
  to full feature set.
- **Custom dashboard card** shipped with the integration (auto-registered, no extra
  install): filters, sorting, drag & drop, card menu with bulk actions, visual config
  editor, 7 languages (EN/DE/FR/ES/IT/NL/PL), fully theme-aware.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Timmes123&repository=ha-better-todo&category=integration)

1. Click the button above (or: HACS → ⋮ → *Custom repositories* → add
   `Timmes123/ha-better-todo` with category *Integration*).
2. Download **Better ToDo** and restart Home Assistant.
3. Add the integration:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=better_todo)

   (or *Settings → Devices & Services → Add Integration → Better ToDo*)

The dashboard card is registered automatically — after an update, hard-refresh your
browser (Ctrl+F5) once so it picks up the new version.

### Manual

Copy `custom_components/better_todo/` into your `config/custom_components/` folder and
restart. HACS is strongly recommended so you get updates.

## The card

| Card menu | Filters |
|:---:|:---:|
| <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/images/card-menu.png" width="340" alt="Card menu with Show filters, Edit lists and Clear completed"> | <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/images/card-filters.png" width="340" alt="Filter bar with list chips, tag chips, person filter and sorting"> |

| Task dialog | List management |
|:---:|:---:|
| <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/images/task-dialog.png" width="340" alt="Task dialog with schedule, reminders, tag picker and rotating assignment"> | <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/images/list-manager.png" width="340" alt="Edit lists dialog"> |

Not a fan of colorful badges? Turn off **Multicolor** in the card editor (or set
`colorful: false`) and every badge switches to your theme's neutral colors:

| Multicolor (default) | Monochrome (`colorful: false`) |
|:---:|:---:|
| <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/images/card-overview.png" width="340" alt="Card with multicolor badges"> | <img src="https://raw.githubusercontent.com/Timmes123/ha-better-todo/main/images/card-overview-mono.png" width="340" alt="Card with monochrome badges in theme colors"> |

The **☰ menu** offers *Show filters* (list/tag/person filter, sorting, view toggles),
*Edit lists* (create, rename, delete — deleting a list removes its tasks and entities),
*Clear completed* (removes all completed tasks in the currently visible lists, with
confirmation) and *Reset filters* (shown while any filter deviates from the defaults).

In the task dialog, **existing tags appear as tappable chips** below the tags field —
no retyping, and a typo stands out immediately as an unexpected extra chip. Assignment
works the same way: tap the persons, and with 2+ selected on a recurring task a
**Rotate** checkbox appears with a **Start with** choice.

Minimal configuration:

```yaml
type: custom:better-todo-card
```

A personal "my tasks" card for a wall tablet:

```yaml
type: custom:better-todo-card
title: My tasks
assigned: me            # tasks assigned to the logged-in user
show_menu: false
show_add: false
sort: due
```

One card per list, side by side (kanban style):

```yaml
type: grid
columns: 2
square: false
cards:
  - type: custom:better-todo-card
    lists: [Household]
    sort: manual        # enables drag & drop reordering
  - type: custom:better-todo-card
    lists: [Healthy Week]
```

There is also a **visual editor** — just add the card from the dashboard card picker and
configure it without YAML.

### All card options

| Option | Default | Description |
|---|---|---|
| `title` | – | Card title |
| `lists` | all | List names or ids to show |
| `tags` | all | Tags to show (any match) |
| `assigned` | `all` | `all`, `me` (logged-in user), `me_unassigned` (logged-in user + unassigned) or a `person.*` entity id |
| `sort` | `smart` | `smart`, `manual` (drag & drop), `due`, `priority`, `title`, `person` |
| `show_menu` | `true` | Card menu (filters, list management, bulk actions) |
| `show_add` | `true` | "+" button to add tasks |
| `show_completed` | `false` | Show completed tasks |
| `show_upcoming` | `false` | Show upcoming/hidden tasks |
| `upcoming_days` | – | Horizon in days for `show_upcoming` (empty = no limit); tasks visible through their own lead window are unaffected |
| `due_soon` | `false` | Start with the "due only" filter active |
| `due_soon_days` | `7` | Lead time in days for the "due only" filter |
| `compact` | `false` | Denser rows |
| `colorful` | `true` | Multicolor badges; `false` = neutral theme colors only |
| `max_height` | – | Max card height in px (scrolls inside) |
| `confirm_complete` | `false` | Ask before completing a task |

## Notifications

Better ToDo sends notifications **itself** — no automations required. Configure them
once under *Settings → Devices & Services → Better ToDo → Configure → Notifications*:

- Pick a **notify service per person** (e.g. the Companion App device,
  `notify.mobile_app_…`). The dash means "no notifications for this person".
- Optionally let **tasks without an assignment** go to every configured person.

Two independent mechanisms build on that mapping:

### Per-task reminders (🔔)

Set up to 5 reminders per task in the task dialog: *at due time*, *X min/h/days
before*. At the configured moment the assigned persons get a push (with rotation, only
the person whose turn it is). Tasks without a due **time** use 09:00 as the reference
point. Reminders are for tasks where the exact moment matters — "trash pickup at 18:00,
remind me 1 h before".

### Daily summary

Enable *Send a daily summary of open tasks* and pick a time (default 08:00). Every day
at that time, each person receives one push listing **their** open tasks:

- **Due and overdue tasks** are always included — an overdue task keeps appearing every
  day (with its "3× due" counter) until it is completed, so nothing silently rots.
- **Weekly/monthly habit tasks** are only included when their period is about to run
  out: weekly tasks in the **last 2 days of the week**, monthly tasks in the **last 5
  days of the month** — and only if they are still open. So "ride the bike once a week"
  stays quiet from Monday to Friday and only shows up on the weekend if you haven't
  done it yet. Completed or skipped periods never appear.
- **No open tasks → no message.** The summary never spams an empty list.

### HA notification center

Optionally the summary is also posted to Home Assistant's notification center (the 🔔
bell in the sidebar) — visible to everyone on the dashboard, even without the Companion
App. It is refreshed at summary time, updates as tasks are completed, and disappears
entirely once nothing is open any more.

### Build your own instead

Everything above also fires as plain HA events (see below), so you can ignore the
built-in notifications and wire up your own automations if you prefer.

## Automations

### Services

```yaml
# Create a task when the washing machine finishes
service: better_todo.add_task
data:
  list: Household           # created automatically if it doesn't exist
  title: Hang up the laundry
  assigned_to: person.alex
```

```yaml
# A recurring task, fully scripted
service: better_todo.add_task
data:
  list: Finance
  title: Pay rent
  type: scheduled
  due_date: "2026-09-01"
  schedule: { freq: monthly, interval: 1, day: 1 }
```

Also available: `better_todo.complete_task`, `better_todo.skip_task`,
`better_todo.remove_task` (by `task_id` or exact `title`; add `list` to scope
the title match to one list).

### Events

| Event | Fired when |
|---|---|
| `better_todo_item_created` | a task is created |
| `better_todo_item_completed` | a task is completed |
| `better_todo_item_due` | a task becomes due (daily at midnight) |
| `better_todo_item_overdue` | a task is overdue (daily at midnight) |
| `better_todo_item_reminder` | a reminder fires (event data includes `offset_minutes`) |

Event data includes `task_id`, `title`, `list_id` and `assigned_to` (a **list** of
person entity ids — use `in`, not `==`, when filtering).

```yaml
alias: ToDo reminders, custom style
triggers:
  - trigger: event
    event_type: better_todo_item_reminder
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: "📝 {{ trigger.event.data.title }}"
      message: >-
        Due {{ trigger.event.data.due }}{% if trigger.event.data.due_time %}
        at {{ trigger.event.data.due_time }}{% endif %}
```

## How the mechanics work

- **Overdue never stacks.** A monthly task you ignored for three months is still *one*
  task, showing "3× due". Completing it once advances one occurrence ("2× due" left);
  "complete all" clears the backlog. The schedule anchor never drifts: schedule-based
  tasks stay locked to their rule, after-completion tasks re-anchor to the day you
  actually completed them.
- **Streaks are honest.** Weekly/monthly tasks track a streak of completed periods. A
  missed period resets the streak and counts up "missed"; deliberately **skipping** a
  period freezes the streak instead — skipping is a decision, not a failure.
- **Multi-assignment is shared.** A task assigned to several persons is one shared task:
  everyone sees it, the first completion completes it for all. Rotation is the opposite
  contract: exactly one owner at a time, handed on after each completion — "Start with"
  picks who begins.
- **Lists are cheap.** Create, rename and delete them from the card menu. Deleting a
  list deletes its tasks and removes the mirrored `todo`/`calendar` entities cleanly.

## Data & backups

All data lives in Home Assistant's storage (`.storage/better_todo`) and is included in
normal HA backups. The `todo`/`calendar` entities are read-write mirrors — deleting them
(or toggling them off in the integration options) never touches your task data.

## Roadmap

- Per-list sensors (open/due/overdue per list & person) and statistics
- Sections inside lists, kanban view
- Actionable notifications (complete/skip straight from the push)
- Optional AI integration via HA `ai_task` entities
- External platform sync (CalDAV and similar) — deliberately last

## Feedback

Questions, ideas or bug reports? Open an
[issue](https://github.com/Timmes123/ha-better-todo/issues) or join the discussion in the
[Home Assistant community thread](https://community.home-assistant.io/t/better-todo-flexible-recurring-tasks-habits-household-rotation-for-ha/1022821).

## ☕ Support

If this integration is useful to you and you want to support its development:

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=kofi&logoColor=white)](https://ko-fi.com/timmes123)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/timmes123)

## License

[MIT](https://github.com/Timmes123/ha-better-todo/blob/main/LICENSE)
