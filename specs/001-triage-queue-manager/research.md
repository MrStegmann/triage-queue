# Research & Technical Decisions: Emergency Unit Triage Queue Manager

**Feature**: Emergency Unit Triage Queue Manager  
**Branch**: `001-triage-queue-manager`  
**Status**: Completed  

---

## 1. Core Priority Queue Data Structure

### Decision
Implement a multi-bucket queue architecture utilizing separate double-ended queues (`collections.deque`) mapped to each discrete triage severity level (`1: Critical`, `2: Urgent`, `3: Standard`), wrapped in a unified `TriageQueue` domain service.

### Rationale
- **Deterministic Priority & Strict FIFO Ordering**: Patients are enqueued directly into their respective triage bucket's tail. Dequeueing and peeking check buckets in ascending order of severity (Level 1, then Level 2, then Level 3), popping from the head of the highest-priority non-empty bucket. This guarantees strict FIFO order within each level with no custom comparator edge cases.
- **Complexity Guarantees**:
  - Enqueue: $O(1)$ amortized append to the designated level bucket.
  - Dequeue / Peek: $O(1)$ worst-case inspection of at most 3 fixed buckets.
  - Statistics: $O(1)$ direct access to bucket lengths (`len(deque)`).
  - Sequence listing: $O(N)$ linear traversal across the 3 buckets without mutating state.
- **Timestamp Immunity**: Because FIFO within a level is maintained by order of entry into the bucket, the queue is completely immune to timestamp resolution limitations, clock jitter, or microsecond collisions.

### Alternatives Considered
- **Python `heapq` with Tuples `(priority, arrival_counter, patient)`**:
  - *Pros*: Standard textbook priority queue.
  - *Cons*: Enqueue is $O(\log N)$, dequeue is $O(\log N)$. Requires an explicit counter sequence to break timestamp ties safely. Queue inspection/listing requires either popping copies or sorting heap elements ($O(N \log N)$). Multi-bucket deque is simpler, faster ($O(1)$), and avoids heap copy/sorting overhead.
- **Single Sorted List (`bisect`)**:
  - *Pros*: Simple sequential array.
  - *Cons*: Enqueue is $O(N)$ due to list element shifting in memory.
- **`queue.PriorityQueue`**:
  - *Pros*: Thread-safe out of the box.
  - *Cons*: Thread synchronization locking adds unnecessary runtime overhead for a single-station in-memory terminal application.

---

## 2. Domain Modeling & Immutability Patterns

### Decision
Use Python 3.12+ features following `python-best-practices`:
- `@dataclass(frozen=True)` for domain entities (`PatientRecord`, `QueueStatistics`).
- An `IntEnum` for `TriageLevel` (`CRITICAL = 1`, `URGENT = 2`, `STANDARD = 3`) with human-readable labels and validation helper methods.
- Immutable state objects preventing accidental field mutation once created.

### Rationale
- Frozen dataclasses prevent accidental mutations of patient attributes (such as arrival time or assigned triage level) once admitted into the queue.
- `IntEnum` enforces discrete, valid triage tiers while allowing intuitive numeric comparison (`level_1 < level_2`) and readable display formatting.
- Fully aligns with project constitution standards for clean domain boundaries.

### Alternatives Considered
- **Standard mutable classes / dicts**:
  - *Cons*: Vulnerable to accidental state mutation during queue inspection, peek, or reporting.
- **Pydantic**:
  - *Cons*: Adds external dependency overhead. Standard library dataclasses satisfy all validation and immutability requirements without external dependencies.

---

## 3. Terminal Interface & Input Handling Architecture

### Decision
Adopt a decoupled Model-View-Controller / Service-CLI architecture:
- **Core Library (`src/triage_queue/`)**: Standalone, independent domain library containing `models.py`, `queue.py`, and domain exceptions. Has zero console/IO dependencies and is 100% unit-testable.
- **Console Interface (`src/triage_queue/cli/`)**: Terminal presentation layer (`menu.py`, `console.py`) handling input prompts, validation loops, formatted terminal display, and user interactions.
- **Standard Library Only**: Pure Python standard library (`sys`, `dataclasses`, `enum`, `collections`, `datetime`, `typing`).

### Rationale
- Aligns with the *Library-First* principle: the triage scheduling engine can be reused directly as the backend for future web or GUI applications without altering queue logic.
- Input validation loops in the CLI cleanly catch invalid inputs (blank names, non-integer or out-of-range triage levels, invalid menu choices) without crashing or corrupting domain state.
- Graceful empty-state responses: Dequeue and peek operations return explicit domain results/None, allowing the CLI to display clear feedback to intake staff.

### Alternatives Considered
- **Single Monolithic Script (`app.py`)**:
  - *Cons*: Tightly couples queue logic with `input()`/`print()` calls, making automated unit testing difficult and hindering future reuse.
- **Third-Party CLI Frameworks (`click`, `typer`, `rich`, `curses`)**:
  - *Cons*: Violates the spec requirement/assumption of standard library runtime with zero external package dependencies. Standard ANSI formatting and clean standard input loops provide a modern, resilient experience without external bloat.

---

## 4. Testing Framework & Strategy

### Decision
Use `pytest` for all test execution, structured into:
- **Unit Tests (`tests/unit/`)**: Comprehensive tests for `PatientRecord` validation, `TriageLevel` enumeration, `TriageQueue` operations (enqueue, dequeue, peek, listing, statistics), and edge cases (empty queue, duplicate timestamps, inverted arrivals).
- **Integration & Workflow Tests (`tests/integration/`)**: Simulates complete patient admission-to-service lifecycles, surge scenarios, and console controller interaction sequences.
- **CLI / Contract Tests (`tests/contract/`)**: Validates terminal menu command behavior and error-recovery loops with mocked I/O (`stdin`/`stdout`).

### Rationale
- Pytest is already installed in the local environment (`pytest 9.1.1`).
- Clean separation of unit, integration, and contract tests supports test-first (TDD) workflow and fast regression execution.

### Alternatives Considered
- **`unittest` standard library**:
  - *Cons*: More boilerplate than `pytest`, though tests will be written in a manner compatible with standard test runners.

---

## 5. Technology Context Summary

| Aspect | Specification |
|---|---|
| **Language** | Python 3.12+ (local runtime: Python 3.14.7) |
| **Dependencies** | None (Python Standard Library only) |
| **Test Framework** | `pytest` |
| **Architecture** | Library-first: Domain Service (`TriageQueue`) + Presentation (`CLI`) |
| **Storage** | In-Memory (single-station intake session) |
| **Platforms** | Cross-platform terminal (Windows, Linux, macOS) |
