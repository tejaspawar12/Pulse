from enum import Enum

class LifecycleStatus(str, Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    ABANDONED = "abandoned"

class CompletionStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"

class RPE(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class SetType(str, Enum):
    WORKING = "working"
    WARMUP = "warmup"
    FAILURE = "failure"
    DROP = "drop"
    AMRAP = "amrap"
