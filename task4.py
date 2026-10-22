import time
import multiprocessing as mp
from multiprocessing import shared_memory
import numpy as np
SIZES = [100_000, 1_000_000, 10_000_000]
REPEATS = 3
def ipc_receiver(conn):
    try:
        while True:
            data = conn.recv()
            if data is None:
                break
            checksum = int(np.sum(data, dtype=np.int64))
            conn.send(checksum)
    finally:
        conn.close()
def shared_memory_receiver(conn):
    shm = None
    try:
        while True:
            message = conn.recv()
            if message is None:
                break
            if message[0] == "attach":
                shm = shared_memory.SharedMemory(name=message[1])
                conn.send("ready")
            elif message[0] == "read":
                array = np.ndarray(
                    message[1],
                    dtype=np.int32,
                    buffer=shm.buf
                )
                checksum = int(np.sum(array, dtype=np.int64))
                conn.send(checksum)
    finally:
        if shm is not None:
            shm.close()
        conn.close()

def benchmark_ipc(array, process, conn):
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        conn.send(array)
        result = conn.recv()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        expected = int(np.sum(array, dtype=np.int64))
        assert result == expected, "IPC checksum mismatch"
    return float(np.median(times))
def benchmark_shared(array, shm, process, conn):
    times = []

    for _ in range(REPEATS):
        start = time.perf_counter()
        conn.send(("read", array.shape))
        result = conn.recv()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        expected = int(np.sum(array, dtype=np.int64))
        assert result == expected, "Shared memory checksum mismatch"
    return float(np.median(times))

def main():
    ctx = mp.get_context("spawn")
    results = []
    print("TASK 4 — Host-to-Host IPC Transfer Profile")
    print("CPU-only mode")
    print(f"Repeats per size: {REPEATS}")
    print("\nStarting benchmarks...")
    for size in SIZES:
        rng = np.random.default_rng(42 + size)
        array = rng.integers(
            1, 101, size=size, dtype=np.int32
        )
        parent_conn, child_conn = ctx.Pipe()
        process = ctx.Process(
            target=ipc_receiver,
            args=(child_conn,)
        )
        process.start()
        child_conn.close()

        try:
            ipc_ms = benchmark_ipc(array, process, parent_conn)
            parent_conn.send(None)
            process.join()
        finally:
            parent_conn.close()
            if process.is_alive():
                process.terminate()
                process.join()

        shm = shared_memory.SharedMemory(
            create=True,
            size=array.nbytes
        )

        shared_array = np.ndarray(
            array.shape,
            dtype=np.int32,
            buffer=shm.buf
        )
        shared_array[:] = array

        parent_conn, child_conn = ctx.Pipe()
        process = ctx.Process(
            target=shared_memory_receiver,
            args=(child_conn,)
        )
        process.start()
        child_conn.close()

        try:
            parent_conn.send(("attach", shm.name))
            assert parent_conn.recv() == "ready"

            shared_ms = benchmark_shared(
                array, shm, process, parent_conn
            )

            parent_conn.send(None)
            process.join()
        finally:
            parent_conn.close()
            if process.is_alive():
                process.terminate()
                process.join()
            shm.close()
            shm.unlink()

        results.append((size, ipc_ms, shared_ms))

        print(f"\nN = {size:,}")
        print(f"Path A — IPC/Pickle: {ipc_ms:.2f} ms")
        print(f"Path B — Shared Memory: {shared_ms:.2f} ms")
        print(f"Transfer overhead difference: {ipc_ms - shared_ms:.2f} ms")

    lines = [
        "TASK 4 — Host-to-Host IPC Transfer Profile",
        "Mode: CPU-only",
        f"Repeats per size: {REPEATS}",
        "Times are median round-trip times, including receiver checksum.",
        "",
        "N | Path A IPC/Pickle (ms) | Path B Shared Memory (ms) | Difference (ms)"
    ]

    for size, ipc_ms, shared_ms in results:
        lines.append(
            f"{size} | {ipc_ms:.2f} | {shared_ms:.2f} | "
            f"{ipc_ms - shared_ms:.2f}"
        )

    with open("task4_output.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")

    print("\nResults saved to task4_output.txt")


if __name__ == "__main__":
    main()
