# Emergency Unit Triage Queue Manager

An in-memory, deterministic triage priority queue and interactive terminal console manager built in Python 3.12+ with zero external runtime dependencies.

## Overview

The **Emergency Unit Triage Queue Manager** prioritizes emergency department patient intake using a 3-tier severity scale:

1. **Level 1 (Critical)**: Immediate resuscitation / life-threatening conditions (highest priority)
2. **Level 2 (Urgent)**: Serious illness / severe pain, rapid attention required
3. **Level 3 (Standard)**: Non-urgent / stable conditions

### Core Features

- **Multi-Priority Queue**: Enqueue patients across tiers; dequeue always dispatches highest clinical severity first.
- **Strict FIFO Preservation**: Multiple patients within the same priority tier are serviced in exact arrival order.
- **Queue Inspection (Peek & Listing)**: Staff can inspect the next patient in line or view the full formatted queue without mutating or altering queue order.
- **Real-Time Workload Statistics**: Instantaneous $O(1)$ reporting of active patient counts by triage tier and total workload.
- **Resilient Terminal UI**: Interactive command console with input validation loops that gracefully reprompt on invalid inputs and handle empty queue states with zero crashes.
- **Zero Runtime Dependencies**: Written entirely in pure Python (standard library `collections.deque`, `dataclasses`, `enum`, `datetime`).

---

## Architecture

The project maintains a strict boundary between the reusable domain library and the CLI presentation layer:

```text
src/
└── triage_queue/
    ├── __init__.py           # Re-exports: TriageQueue, PatientRecord, TriageLevel, QueueStatistics
    ├── exceptions.py         # Domain error hierarchy (ValidationError, EmptyNameError, InvalidTriageLevelError)
    ├── models.py             # Frozen dataclass PatientRecord, IntEnum TriageLevel, QueueStatistics
    ├── queue.py              # Multi-bucket deque TriageQueue aggregate root
    └── cli/
        ├── __init__.py       # CLI exports
        ├── __main__.py       # Execution entry point for `python -m triage_queue.cli`
        ├── console.py        # Terminal formatting and tabular alignment helpers
        ├── main.py           # Standalone entry point (`python src/triage_queue/cli/main.py`)
        └── menu.py           # Interactive menu loop & validation dialogs
```

---

## Quickstart

### Installation

Install the package in editable mode:

```bash
pip install -e .
```

### Running the Terminal Console

Launch the interactive console application:

```bash
python -m triage_queue.cli
```

Or run the script directly:

```bash
python src/triage_queue/cli/main.py
```

### Main Menu Interface

```text
==================================================
   EMERGENCY UNIT TRIAGE QUEUE MANAGER
==================================================
1. Register New Patient (Intake)
2. Call Next Patient for Service (Dequeue)
3. Peek Next Patient in Line
4. View Current Triage Queue
5. View Triage Workload Statistics
6. Exit System
--------------------------------------------------
Select an option (1-6): 
```

---

## Python API Usage

The core priority engine can be imported and used as a standalone library:

```python
from triage_queue import TriageQueue, PatientRecord, TriageLevel

# Initialize queue
queue = TriageQueue()

# Admit patients
p1 = PatientRecord.create("Bob Standard", triage_level=TriageLevel.STANDARD)
p2 = PatientRecord.create("Jane Urgent", triage_level=TriageLevel.URGENT)
p3 = PatientRecord.create("Alice Critical", triage_level=TriageLevel.CRITICAL)

queue.enqueue(p1)
queue.enqueue(p2)
queue.enqueue(p3)

# Peek next patient in line (Alice Critical) without dequeuing
next_up = queue.peek()
print(next_up.name)  # "Alice Critical"

# Dequeue next patient (Critical first, then Urgent, then Standard)
dispatched = queue.dequeue()
print(dispatched.name)  # "Alice Critical"

# Inspect workload statistics
stats = queue.get_statistics()
print(f"Waiting Critical: {stats.critical_count}, Urgent: {stats.urgent_count}, Standard: {stats.standard_count}")
print(f"Total: {stats.total_count}")
```

---

## Running Automated Tests

Run the full automated test suite using `pytest`:

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v
```

All 63 automated tests cover unit validation, public API contracts, CLI terminal contracts, end-to-end integration flows, and quickstart scenarios.
