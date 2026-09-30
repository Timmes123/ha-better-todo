"""Constants for the Better ToDo integration."""

DOMAIN = "better_todo"

SIGNAL_UPDATE = "better_todo_update"

EVENT_CREATED = "better_todo_item_created"
EVENT_COMPLETED = "better_todo_item_completed"
EVENT_DUE = "better_todo_item_due"
EVENT_OVERDUE = "better_todo_item_overdue"
EVENT_REMINDER = "better_todo_item_reminder"

CARD_URL_BASE = "/better_todo_static"
CARD_FILENAME = "better-todo-card.js"

TASK_TYPE_SIMPLE = "simple"
TASK_TYPE_SCHEDULED = "scheduled"
TASK_TYPE_AFTER_COMPLETION = "after_completion"
TASK_TYPE_PERIOD = "period"
TASK_TYPES = [
    TASK_TYPE_SIMPLE,
    TASK_TYPE_SCHEDULED,
    TASK_TYPE_AFTER_COMPLETION,
    TASK_TYPE_PERIOD,
]

FEATURE_PRIORITIES = "priorities"
FEATURE_SUBTASKS = "subtasks"
FEATURE_ASSIGNMENT = "assignment"
FEATURE_ROTATION = "rotation"
FEATURE_PERIODS = "periods"
FEATURE_TAGS = "tags"
FEATURE_TODO_MIRROR = "todo_mirror"
FEATURE_CALENDAR = "calendar"

DEFAULT_FEATURES = {
    FEATURE_PRIORITIES: False,
    FEATURE_SUBTASKS: True,
    FEATURE_ASSIGNMENT: True,
    FEATURE_ROTATION: True,
    FEATURE_PERIODS: True,
    FEATURE_TAGS: True,
    FEATURE_TODO_MIRROR: True,
    FEATURE_CALENDAR: True,
}

DEFAULT_REMINDER_TIME = "09:00"

# Options: how many priority levels the card offers (1 = highest). The
# backend always accepts 1..MAX_PRIORITY so a stored value never breaks
# when the option is lowered again.
CONF_PRIORITY_LEVELS = "priority_levels"
PRIORITY_LEVEL_CHOICES = [3, 5]
DEFAULT_PRIORITY_LEVELS = 3
MAX_PRIORITY = 5

# Per-task location condition for reminders: deliver only while the person
# is inside/outside a zone, otherwise hold the reminder until they are.
LOCATION_MODE_INSIDE = "inside"
LOCATION_MODE_OUTSIDE = "outside"
LOCATION_MODES = [LOCATION_MODE_INSIDE, LOCATION_MODE_OUTSIDE]

# Options: reminder notifications sent by the integration itself.
CONF_NOTIFY_TARGETS = "notify_targets"  # {person_entity_id: notify service name}
CONF_NOTIFY_UNASSIGNED_ALL = "notify_unassigned_all"
NOTIFY_NONE = "-"

# Options: daily summary of open tasks.
CONF_SUMMARY_ENABLED = "summary_enabled"
CONF_SUMMARY_TIME = "summary_time"
CONF_SUMMARY_PERSISTENT = "summary_persistent"
DEFAULT_SUMMARY_TIME = "08:00:00"
SUMMARY_NOTIFICATION_ID = "better_todo_summary"
# Period tasks enter the summary this many days before their period ends.
SUMMARY_PERIOD_LEAD = {"week": 2, "month": 5}

MAX_HISTORY = 5000
