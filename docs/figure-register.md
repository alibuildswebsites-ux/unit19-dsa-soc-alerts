# Figure register and accessible descriptions

All images were generated from source-backed code or actual benchmark-results.json. Charts in Figures 3–6 use the exact measurements captured by `benchmarks/benchmark.py`; there are no illustrative numbers substituted for measurements.

| Figure | Asset | Description / takeaway |
|---|---|---|
| 1 | figure-01-soc-data-flow | Network, identity, EDR and application events enter validation, are recorded by ID, then routed to a severity heap or routine FIFO queue. Both feed the processor and analyst notifications; an array stack supports LIFO analyst-action history. |
| 2 | figure-02-uml-class-diagram | UML-style class view for Alert, AlertEvent, AlertManager, LinkedQueue, PriorityAlertQueue, ArrayStack and the Severity/Status enums. Private state and public operations indicate encapsulation. |
| 3 | figure-03-fifo-scaling | Measured time for a complete enqueue/dequeue batch, comparing linked FIFO and list append/pop(0) at n=250, 1,000, 4,000 and 16,000. |
| 4 | figure-04-priority-scaling | Measured add-all/pop-all cycle for the custom max-heap versus a dynamically sorted list maintained with bisect insertion. |
| 5 | figure-05-sorting-scaling | Actual timing of stable in-place insertion sort and iterative stable merge sort at n=100, 500 and 1,500. |
| 6 | figure-06-memory-profile | tracemalloc peak traced allocations for a built Python list and custom linked queue of 5,000 integer values. |
| 7 | figure-07-shortest-path-example | Weighted network with the highlighted cost-8 shortest route from Sensor to Server; Dijkstra and Bellman–Ford both return 8 on the positive-weight graph. |

Figures are intentionally labelled directly and use shape/annotation in addition to colour. The accompanying report text states what each visual does and does not prove.
