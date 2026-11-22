# Appendix C — Benchmark evidence

The raw output from the reproducible benchmark is stored in `results/benchmark-results.json` and the three corresponding CSV files. The exact benchmark implementation is `benchmarks/benchmark.py`. It uses deterministic input generation, `perf_counter_ns`, five repetitions and median summaries, plus `tracemalloc` peak allocation measurement.
