# Bug Assessment: Concurrency Synchronization for Multi-Worker Queue Operations

- **Slug**: queue-concurrency-lock
- **Created**: 2026-11-03
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

> The choice of three deques and the technical justification are sound, but the issue of concurrency still needs to be addressed: explain how one worker can dequeue an item while another enqueues one—specifically by using a lock around the enqueue/dequeue operations to prevent double processing.

## Symptom

In multi-worker or multi-threaded intake environments, concurrent operations on `TriageQueue` (such as one worker dequeuing while another enqueues, or multiple workers simultaneously dequeuing) can cause race conditions, resulting in duplicate patient processing (double processing), `IndexError: pop from an empty deque`, corrupted counters, or `RuntimeError: deque mutated during iteration`. Under concurrent access, each patient record must be dequeued and processed by exactly one worker, and enqueue/dequeue operations must safely coordinate without data corruption.

## Reproduction

1. Instantiate a shared `TriageQueue` instance.
2. Spawn multiple concurrent worker threads (e.g., using `threading.Thread` or `concurrent.futures.ThreadPoolExecutor`), where worker threads concurrently call `enqueue()` with distinct `PatientRecord` instances while other worker threads concurrently call `dequeue()`.
3. Observe race conditions: two consumer workers can concurrently observe a non-empty bucket and attempt to pop from it simultaneously, leading to `IndexError` or conflicting state, and reader methods iterating over deques (such as `list_all()`) can encounter `RuntimeError: deque mutated during iteration`.

## Suspected Code Paths

- `src/triage_queue/queue.py:9-20` — `TriageQueue.__init__`: Does not initialize any synchronization primitive (e.g., `threading.Lock` or `threading.RLock`) to guard internal bucket collections and counters.
- `src/triage_queue/queue.py:21-26` — `TriageQueue.enqueue()`: Modifies `self._buckets[patient.triage_level]` and increments `self._total_admitted` without mutual exclusion.
- `src/triage_queue/queue.py:28-34` — `TriageQueue.dequeue()`: Multi-step check (`if bucket: return bucket.popleft()`) across three buckets without a lock; two competing workers can interleave checks and pops, causing race conditions and double processing risks.
- `src/triage_queue/queue.py:36-50` — `TriageQueue.peek()` and `TriageQueue.list_all()`: Traverses or inspects deques without locking, allowing concurrent modifications to invalidate state or raise `RuntimeError: deque mutated during iteration`.
- `src/triage_queue/queue.py:52-70` — `TriageQueue.get_statistics()` and `TriageQueue.__len__()`: Non-atomic aggregation across buckets.

## Root Cause Hypothesis

`TriageQueue` was originally designed as an in-memory aggregate for single-station intake (as noted in architectural decisions in `specs/001-triage-queue-manager/research.md`), relying on `collections.deque` without concurrency control. While individual atomic operations on a single deque in CPython are protected by the GIL, compound multi-step operations—such as inspecting multiple priority buckets sequentially, checking emptiness before popping, updating total admitted counters, and iterating over deques for snapshots—are non-atomic across bytecode instructions. Without a mutual exclusion lock, concurrent worker threads interleave during these critical sections, leading to double-processing or race conditions. Confidence: high.

## Proposed Remediation

**Preferred**:
Integrate thread synchronization into `TriageQueue` using Python's standard library `threading.RLock` (re-entrant mutual exclusion lock):
1. In `TriageQueue.__init__`, initialize `self._lock = threading.RLock()`. Using `RLock` allows internal methods (or compound workflows like peeking and conditional dequeueing) to re-enter the lock safely without deadlocking.
2. Wrap critical operations in `with self._lock:`:
   - `enqueue()`: Acquires the lock before appending to the target deque and incrementing `_total_admitted`.
   - `dequeue()`: Acquires the lock before inspecting bucket tiers and popping the head patient, ensuring that only one worker can evaluate and pop a patient at any given moment, strictly preventing double processing.
   - `peek()`, `list_all()`, `get_statistics()`, and `__len__()`: Acquire the lock during reads to guarantee consistent snapshots and prevent iteration errors while other threads enqueue or dequeue.

**How concurrent enqueue and dequeue coordinate with a lock**:
When Worker A (consumer) invokes `dequeue()`, it acquires `self._lock`. While Worker A holds the lock, Worker B (producer) invoking `enqueue()` attempts to acquire `self._lock` and is blocked until Worker A completes its inspection and pop, exiting the `with self._lock:` context. Once Worker A releases the lock, Worker B immediately acquires it, safely appends the patient to the appropriate priority tier, updates counts, and releases the lock. Conversely, if Worker B acquires the lock first, Worker A waits until the new patient is fully enqueued before evaluating the queue. This mutual exclusion ensures atomic state transitions, preserves priority order, and eliminates race windows where two workers could attempt to claim or process the same patient.

**Alternatives**:
- *Alternative 1: Thread-Safe Wrapper Class (`ThreadSafeTriageQueue`)*: Maintain `TriageQueue` as an unsynchronized domain core and provide a thread-safe wrapper/decorator class that synchronizes all calls. *Trade-off*: Keeps base domain logic completely free of threading concerns, but introduces additional classes and requires callers to choose between synchronized and unsynchronized variants.
- *Alternative 2: Standard Library `queue.PriorityQueue`*: Replace the multi-bucket deque architecture with `queue.PriorityQueue`. *Trade-off*: `PriorityQueue` uses a heap with $O(\log N)$ enqueue/dequeue complexity, requires composite priority tuples with sequence counters to maintain FIFO within tiers, and complicates $O(1)$ tier-based statistics and ordered snapshot listing.

**Files likely to change**:
- `src/triage_queue/queue.py`
- `tests/unit/test_queue.py`

**Tests to add or update**:
- Unit/concurrency tests simulating multi-worker environments using `threading.Thread` and `concurrent.futures.ThreadPoolExecutor`.
- Concurrent enqueue/dequeue stress test: multiple worker threads simultaneously admitting and servicing patients, verifying that every enqueued patient is dequeued exactly once with zero double-processing, zero drops, and consistent final queue counts.
- Concurrent reader test: running `list_all()` and `get_statistics()` concurrently with high-throughput enqueue/dequeue loops to verify immunity to `RuntimeError: deque mutated during iteration`.

## Risks & Considerations

- **Contention / Performance**: In a high-throughput multi-worker scenario, acquiring a lock around enqueue and dequeue serializes access to queue state. Given that each operation is $O(1)$ and executes in microseconds in memory, lock contention is negligible for emergency department intake volumes.
- **Deadlock Prevention**: Using `threading.RLock` prevents self-deadlocks if internal methods call each other (e.g., `is_empty()` calling `__len__()`).
- **Immutability of Patient Records**: Because `PatientRecord` instances are `@dataclass(frozen=True)`, once a worker dequeues a patient, the record itself cannot be mutated by other threads.

## Open Questions

- Should the lock be an optional constructor parameter (e.g. `thread_safe=True` or passing an existing lock object) or built directly into `TriageQueue` by default? (Built-in default with `RLock` is standard and zero-cost for single-threaded usage).

