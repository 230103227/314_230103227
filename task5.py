import os
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
TASK_COUNT = 10_000
HASH_ROUNDS = 500
PAYLOAD = b"A" * 1024
def cpu_task(task_id):
    data = PAYLOAD
    digest = b""
    for _ in range(HASH_ROUNDS):
        digest = hashlib.sha256(data).digest()
    return digest[0] + task_id % 256
def run_benchmark(pool_size):
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        results = list(executor.map(cpu_task, range(TASK_COUNT)))
    elapsed_ms = (time.perf_counter() - start) * 1000
    if len(results) != TASK_COUNT:
        raise RuntimeError("Task count verification failed")
    return elapsed_ms, sum(results)
def main():
    cores = os.cpu_count() or 1
    pool_sizes = [
        1,
        max(1, cores // 2),
        cores,
        cores * 2,
        cores * 4,
        cores * 16,
        256
    ]
    pool_sizes = sorted(set(pool_sizes))
    print("TASK 5 — Thread Oversubscription Threshold")
    print(f"Logical CPU cores: {cores}")
    print(f"CPU-bound tasks: {TASK_COUNT:,}")
    print(f"SHA-256 rounds per task: {HASH_ROUNDS}")
    print(f"Unique pool sizes: {pool_sizes}")
    results = []
    for pool_size in pool_sizes:
        elapsed_ms, checksum = run_benchmark(pool_size)
        results.append((pool_size, elapsed_ms, checksum))
        print(f"Completed pool size {pool_size}: {elapsed_ms:.2f} ms")
    baseline_time = results[0][1]
    first_worsening = None
    for i in range(1, len(results)):
        if results[i][1] > results[i - 1][1]:
            first_worsening = results[i][0]
            break
    lines = [
        "TASK 5 — Thread Oversubscription Threshold",
        f"Logical CPU cores: {cores}",
        f"CPU-bound tasks: {TASK_COUNT}",
        f"SHA-256 rounds per task: {HASH_ROUNDS}",
        "",
        f"{'Pool Size':>12} | {'Execution Time (ms)':>20} | "
        f"{'Speedup':>10} | Status",
        "-" * 75
    ]

    for i, (pool_size, elapsed_ms, checksum) in enumerate(results):
        speedup = baseline_time / elapsed_ms if elapsed_ms > 0 else 0.0
        if pool_size == first_worsening:
            status = "FIRST WORSENING"
        elif i > 0 and elapsed_ms > results[i - 1][1]:
            status = "SLOWER"
        else:
            status = "OK"
        lines.append(
            f"{pool_size:12d} | {elapsed_ms:20.2f} | "
            f"{speedup:9.2f}x | {status}"
        )
    lines.append("")
    if first_worsening is not None:
        lines.append(
            f"First observed worsening: pool size {first_worsening}"
        )
        lines.append(
            "This is the first tested pool size slower than the previous "
            "tested size."
        )
    else:
        lines.append(
            "No worsening observed between consecutive tested pool sizes."
        )

    lines.append(
        "Note: timing alone cannot prove that OS context switching "
        "is the sole cause."
    )

    output = "\n".join(lines)

    with open("task5_output.txt", "w", encoding="utf-8") as file:
        file.write(output + "\n")

    print("\n" + output)
    print("\nResults saved to task5_output.txt")


if __name__ == "__main__":
    main()
