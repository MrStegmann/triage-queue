# Interface Contract: Core Triage Queue Library API

**Contract Type**: Python Public Library API  
**Namespace**: `triage_queue`  
**Status**: Stable  

---

## 1. Module Architecture

The core triage queue library is encapsulated within the `triage_queue` package and exposes a clean public interface:

```text
src/triage_queue/
├── __init__.py           # Re-exports TriageQueue, PatientRecord, TriageLevel, exceptions
├── exceptions.py         # Domain error hierarchy
├── models.py             # TriageLevel, PatientRecord, QueueStatistics
└── queue.py              # TriageQueue aggregate implementation
```

---

## 2. Types & Models API

### 2.1 `TriageLevel`

```python
from enum import IntEnum

class TriageLevel(IntEnum):
    CRITICAL = 1
    URGENT = 2
    STANDARD = 3

    @classmethod
    def from_value(cls, val: int | str) -> "TriageLevel":
        """Parse integer or string into TriageLevel, raising InvalidTriageLevelError if invalid."""
        ...

    @property
    def label(self) -> str:
        """Return human-readable label: 'Critical', 'Urgent', or 'Standard'."""
        ...
```

### 2.2 `PatientRecord`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class PatientRecord:
    id: str
    name: str
    triage_level: TriageLevel
    arrived_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        triage_level: TriageLevel | int,
        arrived_at: Optional[datetime] = None,
        patient_id: Optional[str] = None,
    ) -> "PatientRecord":
        """Factory method performing parameter validation and default timestamp assignment."""
        ...
```

### 2.3 `QueueStatistics`

```python
@dataclass(frozen=True)
class QueueStatistics:
    critical_count: int
    urgent_count: int
    standard_count: int
    total_count: int
```

---

## 3. Exceptions API

```python
class TriageQueueError(Exception):
    """Base exception for all domain errors within triage_queue."""
    pass

class ValidationError(TriageQueueError):
    """Raised when an entity fails validation."""
    pass

class EmptyNameError(ValidationError):
    """Raised when a patient name is empty or contains only whitespace."""
    pass

class InvalidTriageLevelError(ValidationError):
    """Raised when a triage level is outside {1, 2, 3} or cannot be parsed."""
    pass
```

---

## 4. `TriageQueue` API Contract

```python
from typing import Optional, Sequence

class TriageQueue:
    def __init__(self) -> None:
        """Initialize an empty triage queue with discrete priority buckets."""
        ...

    def enqueue(self, patient: PatientRecord) -> None:
        """
        Add a patient to the queue at the end of their respective triage tier.
        
        Args:
            patient: Immutable PatientRecord to add.
            
        Raises:
            TypeError: If patient is not an instance of PatientRecord.
        """
        ...

    def dequeue(self) -> Optional[PatientRecord]:
        """
        Remove and return the highest-priority patient waiting the longest.
        
        Returns:
            The next PatientRecord in priority and FIFO order, or None if the queue is empty.
        """
        ...

    def peek(self) -> Optional[PatientRecord]:
        """
        Return the next patient due for service without removing them from the queue.
        
        Returns:
            The next PatientRecord in line, or None if the queue is empty.
        """
        ...

    def list_all(self) -> Sequence[PatientRecord]:
        """
        Return an immutable snapshot sequence of all waiting patients in service order.
        
        Returns:
            Tuple of PatientRecord objects ordered strictly by clinical priority then arrival.
        """
        ...

    def get_statistics(self) -> QueueStatistics:
        """
        Return aggregate summary counts by triage tier.
        
        Returns:
            QueueStatistics snapshot instance.
        """
        ...

    def is_empty(self) -> bool:
        """Return True if no patients are currently waiting, False otherwise."""
        ...

    def __len__(self) -> int:
        """Return the total number of waiting patients across all tiers."""
        ...
```
