import os
import time
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from math import pi

SAMPLES = 40_000_000
THREADS = 4
BATCH_SIZE = 10_000
def count_inside(points):
    return int(np.count_nonzero(
        points[:, 0] * points[:, 0] +
        points[:, 1] * points[:, 1] <= 1.0
    ))
def shared_prng_simulation():
    rng = np.random.default_rng(42)
    lock = threading.Lock()
    counts = [0] * THREADS
    samples_per_thread = SAMPLES // THREADS
    def worker(index):
        inside = 0
        remaining = samples_per_thread
        while remaining > 0:
            batch = min(BATCH_SIZE, remaining)
            with lock:
                points = rng.random((batch, 2))

            inside += count_inside(points)
            remaining -= batch

        counts[index] = inside

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        list(executor.map(worker, range(THREADS)))

    elapsed_ms = (time.perf_counter() - start) * 1000
    total_inside = sum(counts)
    estimate = 4.0 * total_inside / SAMPLES

    return estimate, abs(estimate - pi), elapsed_ms


def independent_prng_simulation(student_id):
    counts = [0] * THREADS
    samples_per_thread = SAMPLES // THREADS

    def worker(index):
        seed = student_id * 10 + index
        rng = np.random.default_rng(seed)
        inside = 0
        remaining = samples_per_thread

        while remaining > 0:
            batch = min(BATCH_SIZE, remaining)
            points = rng.random((batch, 2))
            inside += count_inside(points)
            remaining -= batch

        counts[index] = inside

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        list(executor.map(worker, range(THREADS)))

    elapsed_ms = (time.perf_counter() - start) * 1000
    total_inside = sum(counts)
    estimate = 4.0 * total_inside / SAMPLES

    return estimate, abs(estimate - pi), elapsed_ms


def main():
    raw_id = input("Enter your numeric Student ID: ").strip()

    try:
        student_id = int(raw_id)
        if student_id < 0:
            raise ValueError
    except ValueError:
        print("Please enter a non-negative numeric Student ID.")
        return

    print("\nTASK 2 — PRNG State Bottleneck")
    print(f"Student ID: {student_id}")
    print(f"Logical CPU count: {os.cpu_count()}")
    print(f"Sample points: {SAMPLES:,}")
    print(f"Threads: {THREADS}")
    shared_pi, shared_error, shared_ms = shared_prng_simulation()
    independent_pi, independent_error, independent_ms = (
        independent_prng_simulation(student_id)
    )
    speedup = (
        shared_ms / independent_ms
        if independent_ms > 0
        else float("inf")
    )
    lines = [
        "TASK 2 — PRNG State Bottleneck",
        f"Student ID: {student_id}",
        f"Logical CPU count: {os.cpu_count()}",
        f"Sample points: {SAMPLES}",
        f"Threads: {THREADS}",
        "",
        f"Shared PRNG computed pi: {shared_pi:.10f}",
        f"Shared PRNG absolute error: {shared_error:.10f}",
        f"Shared PRNG wall time: {shared_ms:.2f} ms",
        "",
        f"Independent PRNG computed pi: {independent_pi:.10f}",
        f"Independent PRNG absolute error: {independent_error:.10f}",
        f"Independent PRNG wall time: {independent_ms:.2f} ms",
        "",
        f"Speedup factor: {speedup:.2f}x",
    ]

    output = "\n".join(lines)
    print("\n" + output)

    with open("task2_output.txt", "w", encoding="utf-8") as file:
        file.write(output + "\n")

    print("\nResults saved to task2_output.txt")


if __name__ == "__main__":
    main()
