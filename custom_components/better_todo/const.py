"""Constants for the Better ToDo integration."""

DOMAIN = "better_todo"

SIGNAL_UPDATE = "better_todo_update"

EVENT_CREATED = "better_todo_item_created"
EVENT_COMPLETED = "better_todo_item_completed"
EVENT_DUE = "better_todo_item_due"
EVENT_OVERDUE = "better_todo_item_overdue"

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

DEFAULT_FEATURES = {
    FEATURE_PRIORITIES: False,
    FEATURE_SUBTASKS: True,
    FEATURE_ASSIGNMENT: True,
    FEATURE_ROTATION: True,
    FEATURE_PERIODS: True,
}

MAX_HISTORY = 5000
