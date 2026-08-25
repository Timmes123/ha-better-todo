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
