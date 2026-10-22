import os
import sys
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
SIZE = 2_000_000
def serial_scan(array):
    output = np.empty(len(array), dtype=np.int64)
    output[0] = array[0]
    for i in range(1, len(array)):
        output[i] = output[i - 1] + array[i]
    return output
def local_scan(array):
    local_output = np.cumsum(array, dtype=np.int64)
    local_sum = int(local_output[-1])
    return local_output, local_sum
def apply_offset(data):
    chunk, offset = data
    if offset != 0:
        chunk += offset
    return chunk
def parallel_scan(array, workers):
    chunks = np.array_split(array, workers)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        local_results = list(executor.map(local_scan, chunks))

    local_outputs = [result[0] for result in local_results]
    chunk_sums = [result[1] for result in local_results]

    offsets = []
    running_sum = 0
    for chunk_sum in chunk_sums:
        offsets.append(running_sum)
        running_sum += chunk_sum
    offset_data = list(zip(local_outputs, offsets))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        adjusted_chunks = list(executor.map(apply_offset, offset_data))
    return np.concatenate(adjusted_chunks)
def main():
    raw_id = input("Enter your numeric Student ID: ").strip()
    try:
        student_id = int(raw_id)
        if student_id < 0:
            raise ValueError
    except ValueError:
        print("Student ID must be a non-negative integer.")
        sys.exit(1)
    rng = np.random.default_rng(student_id)
    array = rng.integers(1, 11, size=SIZE, dtype=np.int64)
    try:
        import psutil
        workers = psutil.cpu_count(logical=False) or 1
    except ImportError:
        workers = os.cpu_count() or 1
    workers = max(1, min(workers, SIZE))
    print("\nTASK 3 — Prefix Scan")
    print(f"Student ID: {student_id}")
    print(f"Array size: {SIZE:,}")
    print(f"Parallel workers: {workers}")

    start = time.perf_counter()
    serial_output = serial_scan(array)
    serial_time = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    parallel_output = parallel_scan(array, workers)
    parallel_time = (time.perf_counter() - start) * 1000
    speedup = (
        serial_time / parallel_time
        if parallel_time > 0
        else float("inf")
    )
    output_lines = [
        "TASK 3 — Prefix Scan",
        f"Student ID: {student_id}",
        f"Array size: {SIZE}",
        f"Parallel workers: {workers}",
        f"Serial Time: {serial_time:.2f} ms",
        f"Parallel Time: {parallel_time:.2f} ms",
        f"Speedup: {speedup:.2f}x",
    ]

    try:
        assert parallel_output[-1] == serial_output[-1]
        output_lines.append("Verification Status: PASS")
    except AssertionError:
        output_lines.append("Verification Status: FAIL")
        with open("task3_output.txt", "w", encoding="utf-8") as file:
            file.write("\n".join(output_lines) + "\n")
        print("\n".join(output_lines))
        sys.exit(1)

    with open("task3_output.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(output_lines) + "\n")

    print()
    print("\n".join(output_lines))


if __name__ == "__main__":
    main()
