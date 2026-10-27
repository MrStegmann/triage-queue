# Implementation Plan: Emergency Unit Triage Queue Manager

**Branch**: `001-triage-queue-manager` | **Date**: 2026-10-27 | **Spec**: [spec.md](file:///j:/GitHub/triage-queue/specs/001-triage-queue-manager/spec.md)

**Input**: Feature specification from `/specs/001-triage-queue-manager/spec.md`

---

## Summary

Build a robust, terminal-based Python triage queue manager for emergency unit intake. The system implements a deterministic multi-priority queue (Level 1: Critical > Level 2: Urgent > Level 3: Standard) with strict FIFO ordering within each tier, an interactive terminal console with input validation loops, and queue inspection/reporting capabilities. The technical approach uses a multi-bucket deque design (`collections.deque`) in pure standard library Python, separating the core scheduling library from the terminal CLI.

---

## Technical Context

**Language/Version**: Python 3.12+ (local runtime: Python 3.14.7)

**Primary Dependencies**: None (Python standard library only: `sys`, `dataclasses`, `enum`, `collections`, `datetime`, `typing`, `uuid`)

**Storage**: In-memory data structures (single-station session scope)

**Testing**: `pytest` (local version: 9.1.1)

**Target Platform**: Cross-platform terminal (Windows PowerShell/cmd, Linux, macOS)

**Project Type**: Standalone library (`triage_queue`) with interactive terminal CLI (`triage_queue.cli`)

**Performance Goals**:
- $O(1)$ patient admission (enqueue)
- $O(1)$ patient service call (dequeue)
- $O(1)$ next patient inspection (peek)
- $O(1)$ triage tier statistics calculation
- Instantaneous terminal menu rendering (<50ms)

**Constraints**:
- Zero external package runtime dependencies
- Zero unhandled exceptions or crashes on empty queue operations or invalid user input
- Strict immutability for patient records once admitted (`@dataclass(frozen=True)`)

**Scale/Scope**: Single-station emergency intake supporting hundreds of concurrently queued patients during operational shifts

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle / Gate | Requirement | Evaluation | Status |
|---|---|---|---|
| **I. Library-First** | Standalone domain library independent of presentation / IO | Core queue logic isolated in `triage_queue/` with zero CLI dependencies | **PASS** |
| **II. CLI Interface** | Accessible terminal menu with clear user prompts, status, and error reporting | Interactive console with validation loops and graceful error handling | **PASS** |
| **III. Test-First (TDD)** | Verification via automated tests before implementation completion | Unit, integration, and contract test suites covering all functional requirements | **PASS** |
| **IV. Simplicity (YAGNI)** | Minimal dependencies, clean architecture without premature overengineering | Standard library multi-bucket deque; no external heavy frameworks or persistence layer needed for v1 | **PASS** |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-triage-queue-manager/
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 technical research & data structure decisions
├── data-model.md        # Phase 1 domain entities, states & invariants
├── quickstart.md        # Phase 1 runnable validation scenarios & guide
├── contracts/           # Phase 1 interface specifications
│   ├── queue-api.md     # Public Python library API contract
│   └── cli-contract.md  # Terminal console interface & menu contract
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code (repository root)

```text
src/
└── triage_queue/
    ├── __init__.py           # Package exports (TriageQueue, PatientRecord, TriageLevel)
    ├── exceptions.py         # Domain exceptions (EmptyNameError, InvalidTriageLevelError)
    ├── models.py             # PatientRecord, TriageLevel enum, QueueStatistics
    ├── queue.py              # TriageQueue aggregate with multi-bucket priority logic
    └── cli/
        ├── __init__.py       # CLI module entry points
        ├── __main__.py       # Execution entry point for `python -m triage_queue.cli`
        ├── console.py        # Terminal formatting, table output, and display helpers
        ├── main.py           # Standalone entry script (`python src/triage_queue/cli/main.py`)
        └── menu.py           # Interactive menu loop and resilient input dialogs

tests/
├── conftest.py               # Shared test fixtures (sample patients, queue instances)
├── contract/
│   ├── test_cli_contract.py  # Contract tests for terminal menu actions and mocked IO
│   └── test_queue_api.py     # Public API contract tests for TriageQueue
├── integration/
│   └── test_triage_flow.py   # Full intake-to-dispatch lifecycle and surge tests
└── unit/
    ├── test_models.py        # PatientRecord and TriageLevel validation tests
    └── test_queue.py         # Core TriageQueue priority, FIFO, and edge-case tests
```

**Structure Decision**: Selected a modular single-project layout that enforces clear boundaries between the domain scheduling core (`triage_queue`) and the console user experience (`triage_queue.cli`), directly enabling future headless, API, or web integrations without refactoring queue logic.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. Standard library architecture complies with all principles.*
