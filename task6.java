import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;
public class task6 {
    private static final int THREADS = 8;
    private static final int INCREMENTS_PER_THREAD = 1_000_000;
    private static final long TOTAL_OPS =
            (long) THREADS * INCREMENTS_PER_THREAD;
    private static class Result {
        long counter;
        double timeMs;
        double throughput;
        Result(long counter, double timeMs) {
            this.counter = counter;
            this.timeMs = timeMs;
            this.throughput = TOTAL_OPS / (timeMs / 1000.0);
        }
    }
    private static Result benchmarkMutex() throws InterruptedException {
        ReentrantLock lock = new ReentrantLock();
        long[] counter = {0};
        CountDownLatch ready = new CountDownLatch(THREADS);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(THREADS);
        List<Thread> workers = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            Thread worker = new Thread(() -> {
                ready.countDown();
                try {
                    start.await();
                    for (int j = 0; j < INCREMENTS_PER_THREAD; j++) {
                        lock.lock();
                        try {
                            counter[0]++;
                        } finally {
                            lock.unlock();
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    done.countDown();
                }
            });

            workers.add(worker);
            worker.start();
        }

        ready.await();
        long begin = System.nanoTime();
        start.countDown();
        done.await();
        long end = System.nanoTime();

        for (Thread worker : workers) {
            worker.join();
        }

        double timeMs = (end - begin) / 1_000_000.0;
        return new Result(counter[0], timeMs);
    }

    private static Result benchmarkAtomic() throws InterruptedException {
        AtomicInteger counter = new AtomicInteger(0);

        CountDownLatch ready = new CountDownLatch(THREADS);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(THREADS);

        List<Thread> workers = new ArrayList<>();

        for (int i = 0; i < THREADS; i++) {
            Thread worker = new Thread(() -> {
                ready.countDown();

                try {
                    start.await();

                    for (int j = 0; j < INCREMENTS_PER_THREAD; j++) {
                        counter.incrementAndGet();
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    done.countDown();
                }
            });

            workers.add(worker);
            worker.start();
        }

        ready.await();
        long begin = System.nanoTime();
        start.countDown();
        done.await();
        long end = System.nanoTime();

        for (Thread worker : workers) {
            worker.join();
        }

        double timeMs = (end - begin) / 1_000_000.0;
        return new Result(counter.get(), timeMs);
    }

    public static void main(String[] args) {
        try {
            System.out.println("TASK 6 — Mutex vs. Atomic CAS");
            System.out.println("Threads: " + THREADS);
            System.out.println(
                    "Increments per thread: " + INCREMENTS_PER_THREAD);
            System.out.println("Total operations per test: " + TOTAL_OPS);
            System.out.println();
            Result mutex = benchmarkMutex();
            Result atomic = benchmarkAtomic();
            if (mutex.counter != TOTAL_OPS ||
                    atomic.counter != TOTAL_OPS) {
                System.err.println("ERROR: Counter verification failed.");
                System.exit(1);
            }

            double ratio = atomic.throughput / mutex.throughput;

            List<String> lines = List.of(
                    "TASK 6 — Mutex vs. Atomic CAS",
                    "Threads: " + THREADS,
                    "Increments per thread: " + INCREMENTS_PER_THREAD,
                    "Total operations per test: " + TOTAL_OPS,
                    "",
                    String.format(
                            "Mutex Execution Time: %.2f ms", mutex.timeMs),
                    String.format(
                            "Mutex Throughput: %.2f ops/sec",
                            mutex.throughput),
                    "Mutex Final Counter: " + mutex.counter,
                    "",
                    String.format(
                            "Atomic CAS Execution Time: %.2f ms",
                            atomic.timeMs),
                    String.format(
                            "Atomic CAS Throughput: %.2f ops/sec",
                            atomic.throughput),
                    "Atomic Final Counter: " + atomic.counter,
                    "",
                    String.format("Throughput Ratio: %.4fx", ratio)
            );

            String output = String.join("\n", lines);
            System.out.println(output);

            Files.writeString(
                    Path.of("task6_output.txt"),
                    output + System.lineSeparator()
            );

            System.out.println("\nResults saved to task6_output.txt");

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.err.println("Benchmark interrupted.");
            System.exit(1);
        } catch (IOException e) {
            System.err.println("Could not save output: " + e.getMessage());
            System.exit(1);
        }
    }
}
