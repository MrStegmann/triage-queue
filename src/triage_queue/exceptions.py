"""Domain error hierarchy for triage_queue."""


class TriageQueueError(Exception):
    """Base exception for all domain errors within triage_queue."""


class ValidationError(TriageQueueError):
    """Raised when an entity fails validation."""


class EmptyNameError(ValidationError):
    """Raised when a patient name is empty or contains only whitespace."""


class InvalidTriageLevelError(ValidationError):
    """Raised when a triage level is outside {1, 2, 3} or cannot be parsed."""
