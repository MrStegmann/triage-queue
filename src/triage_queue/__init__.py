"""Emergency Unit Triage Queue Manager package."""

from triage_queue.exceptions import (
    EmptyNameError,
    InvalidTriageLevelError,
    TriageQueueError,
    ValidationError,
)
from triage_queue.models import PatientRecord, QueueStatistics, TriageLevel
from triage_queue.queue import TriageQueue

__all__ = [
    "EmptyNameError",
    "InvalidTriageLevelError",
    "PatientRecord",
    "QueueStatistics",
    "TriageLevel",
    "TriageQueue",
    "TriageQueueError",
    "ValidationError",
]

