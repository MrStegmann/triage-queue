# Bug Fix: Concurrency Synchronization for Multi-Worker Queue Operations

- **Slug**: queue-concurrency-lock
- **Fixed**: 2026-11-03
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Integrated `threading.RLock` into `TriageQueue` to protect all internal state transitions and iterations. This enables concurrent multi-worker intake and dispatch, strictly preventing double processing, dropped records, and race conditions between workers.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/triage_queue/queue.py` | modified | Added `self._lock = threading.RLock()` in `__init__` and wrapped `enqueue`, `dequeue`, `peek`, `list_all`, `get_statistics`, `is_empty`, and `__len__` within `with self._lock:` |
| `tests/unit/test_queue.py` | modified | Added `TestTriageQueueConcurrency` covering multi-threaded producer/consumer stress tests, reader snapshot concurrency, and simultaneous barrier synchronization |

## Diff Highlights (optional)

```python
class TriageQueue:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._buckets: Dict[TriageLevel, Deque[PatientRecord]] = {
            TriageLevel.CRITICAL: deque(),
            TriageLevel.URGENT: deque(),
            TriageLevel.STANDARD: deque(),
        }
        self._total_admitted: int = 0

    def enqueue(self, patient: PatientRecord) -> None:
        if not isinstance(patient, PatientRecord):
            raise TypeError(f"Expected PatientRecord instance, got {type(patient).__name__}")
        with self._lock:
            self._buckets[patient.triage_level].append(patient)
            self._total_admitted += 1

    def dequeue(self) -> Optional[PatientRecord]:
        with self._lock:
            for level in (TriageLevel.CRITICAL, TriageLevel.URGENT, TriageLevel.STANDARD):
                bucket = self._buckets[level]
                if bucket:
                    return bucket.popleft()
            return None
```

## Tests Added or Updated

- `tests/unit/test_queue.py::TestTriageQueueConcurrency::test_concurrent_enqueue_and_dequeue_multi_worker` — Validates 4 producer and 4 consumer threads processing 200 items concurrently; verifies zero double-processing (`set` size matches total count) and zero lost patients.
- `tests/unit/test_queue.py::TestTriageQueueConcurrency::test_concurrent_readers_during_mutations` — Validates that concurrent readers executing `list_all()`, `peek()`, and `get_statistics()` do not raise `RuntimeError: deque mutated during iteration` or return inconsistent statistics.
- `tests/unit/test_queue.py::TestTriageQueueConcurrency::test_coordinating_enqueue_while_dequeuing` — Validates exact mutual exclusion when one thread dequeues while another enqueues simultaneously using a `threading.Barrier`.

## Local Verification

- Commands run: `uv run --with pytest pytest` → 66 passed in 0.71s
- Manual checks: Verified thread safety across all tiers and snapshot consistency during stress execution.

## Deviations from Assessment

None.

## Follow-ups

- If the service evolves from a multi-threaded in-memory service into a multi-process distributed service, migrate synchronization to an external distributed lock or broker (e.g., Redis).

