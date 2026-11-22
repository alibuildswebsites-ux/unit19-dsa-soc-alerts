"""Build the matching Word and PDF technical report from a shared content model."""
from __future__ import annotations
import json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.deps'))
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    PageBreak, Image, Table, TableStyle, Preformatted, KeepTogether, Flowable)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

NAVY='18324A'; INK=NAVY; TEAL='087F8C'; SLATE='627588'; PALE='F3F7F9'; LIGHT='DCE6EB'; AMBER='C58B3D'; WHITE='FFFFFF'; GREEN='3A806C'

# Canonical document content. Body sections 1-7 are counted toward the 4,000–5,500 word target;
# references and appendices are outside the main-body count, as is conventional for this report.
B=[]
def H1(t): B.append(('h1',t))
def H2(t): B.append(('h2',t))
def P(t): B.append(('p',t))
def BUL(*items): B.append(('bullets',list(items)))
def CODE(t): B.append(('code',t.strip('\n')))
def TABLE(caption,headers,rows,widths=None): B.append(('table',caption,headers,rows,widths))
def FIG(n,caption,desc,width=6.15): B.append(('figure',n,caption,desc,width))
def PB(): B.append(('pagebreak',))

H1('1. Introduction and requirements interpretation')
P("This report designs, implements and evaluates a small backend for a Security Operations Centre (SOC) alert-management service. The scenario in the Pearson brief has two competing operational needs: routine events must be retained and processed in arrival order, while high-severity incidents must move ahead of lower-risk work. The design therefore uses two explicit scheduling policies rather than forcing every alert through one undifferentiated list. It also records alert identifiers, lifecycle status and timestamps, and publishes updates to analyst observers (Pearson, 2024).")
P("A SOC needs predictable ordering, safe state changes, traceability and bounded overload behaviour. A theoretically efficient structure can still be slower in a particular runtime or consume more memory. The evaluation combines asymptotic analysis, timing, traced-memory measurement and edge-case tests (Leiss, 2007; Heineman, Pollice and Selkow, 2009).")
P("The implementation uses Python 3.12 and pytest. Type hints, frozen data classes and exceptions keep the logic readable. The linked queue, array stack and binary heap are implemented directly; locks, timestamps and the ID dictionary use standard-library support (Python Software Foundation, 2024a; 2024b).")
P("The report follows the four tasks and maps them to LO1–LO4. The assessment grid on pages 6–7 of the supplied brief is also addressed: a concrete FIFO example, the software call stack, two sorting algorithms, two shortest-path algorithms, imperative ADT specifications, encapsulation, the relation between ADTs and object orientation, trade-offs, and benefits of implementation-independent designs. Full source files, test evidence, benchmark data and diagram source are retained under the project appendices and evidence folders.")

H1('2. Task 1 — analysis and selection of data structures')
H2('2.1 Data types and the alert record')
P("An alert stores an ID, enumerated severity, timezone-aware received/updated timestamps and a lifecycle status (QUEUED, IN_PROGRESS, RESOLVED or DISMISSED). The frozen Alert dataclass makes changes create replacement snapshots rather than silently mutating a record. Python describes frozen dataclasses as read-only emulation, not absolute memory immutability (Python Software Foundation, 2024a).")
P("The chosen severity order is INFO < LOW < MEDIUM < HIGH < CRITICAL. The manager routes HIGH and CRITICAL alerts to the priority heap; INFO, LOW and MEDIUM alerts enter the routine FIFO queue. This threshold is a policy decision for the scenario, not a claim that all SOCs use identical severity taxonomies. The received timestamp is retained separately from the update timestamp: the first explains when the source event arrived, while the latter records when the system last changed its lifecycle state.")

H2('2.2 Arrays')
P("Arrays store indexed elements and provide O(1) access by index. Traversal and unsorted search are O(n); middle insertion/deletion is O(n) because elements shift. Dynamic arrays amortise append to O(1), although resizing costs O(n). Arrays suit fixed tables, histograms, time buckets and caches (Cormen, Leiserson and Rivest, 1990; Wirth, 2004).")
P("The stack in this project is backed by a fixed-length Python list, which gives the demonstration direct array indexing while enforcing a clear capacity. It preallocates a slot for each permitted history item. This trades unused reserved slots for a simple overflow condition and predictable maximum history size. An ordinary Python list is also used as a benchmark alternative, but that does not replace the custom array-backed stack implementation.")
CODE("values = [\"alert-A\", \"alert-B\", \"alert-C\"]\nprint(values[1])\nvalues.insert(1, \"alert-X\")\nprint(values)")
P("Actual interpreter output: `alert-B` followed by `['alert-A', 'alert-X', 'alert-B', 'alert-C']`. The example shows constant-time indexed read and the visible shifting required by a middle insertion; it is an illustrative operation, not a performance measurement.")

H2('2.3 Linked lists')
P("A singly linked list stores values in nodes with next references. With head and tail pointers, tail insertion and head removal are O(1), while search and indexed access are O(n). A doubly linked list adds a previous pointer, increasing storage but enabling O(1) removal of a known node. Linked lists grow without contiguous allocation but incur pointer, allocation and cache-locality costs (Cormen, Leiserson and Rivest, 1990; Sedgewick, 1983).")
P("The routine queue uses a singly linked representation with both head and tail. Enqueue links a new node after the tail; dequeue advances the head. When the last node is removed, both head and tail are reset to None. This final reset is essential: otherwise a later enqueue could attach to a detached node and the empty-to-non-empty transition would corrupt the queue. A capacity check is performed before allocation, making overload explicit rather than allowing an unbounded queue to consume memory indefinitely.")

H2('2.4 Stacks and LIFO behaviour')
P("A stack exposes push, pop and peek at one end and follows last-in-first-out (LIFO). An array stack has O(1) top operations and O(C) preallocated storage; a linked stack grows dynamically but adds node overhead. Stacks suit undo histories, parsing, depth-first traversal and runtime calls (Sedgewick, 1983; Wirth, 2004).")
P("The analyst-action history uses a bounded array stack. If an analyst records “acknowledge AUTH-100” and then “assign EDR-501”, the next undo returns “assign EDR-501” first. This is LIFO because undo reverses the newest action before the older action. The sample execution in Appendix B records that exact order. The bound is intentional: it prevents the demonstration history from growing without limit, and a production system could persist an action audit trail separately rather than treating an in-memory undo stack as the authoritative record.")
P("A function call pushes a frame containing return information, arguments and local state. Nested calls push newer frames; returning pops the newest frame and resumes its caller. Recursion therefore uses nested LIFO frames. The application's ArrayStack illustrates the ordering principle but is not the Python interpreter's runtime stack.")

H2('2.5 Queues and FIFO behaviour')
P("A queue inserts at the rear and removes from the front (FIFO). A linked queue with head/tail references achieves O(1) enqueue and dequeue. A circular array can also provide O(1) operations but needs capacity and full/empty handling. Removing index zero from a plain list shifts remaining elements, making a full drain O(n²) (Cormen, Leiserson and Rivest, 1990).")
P("A concrete FIFO example is the arrival sequence A, B, C. Enqueue(A), enqueue(B), enqueue(C) yields the queue [A, B, C]; three consecutive dequeue operations return A, then B, then C. A SOC routine stream uses this rule to preserve fairness and traceability among events assigned to the routine path. It does not mean the whole platform is globally FIFO: high-severity incidents are intentionally handled by a separate priority policy.")
CODE("queue = LinkedQueue()\nqueue.enqueue(\"A\")\nqueue.enqueue(\"B\")\nqueue.enqueue(\"C\")\nprint([queue.dequeue() for _ in range(3)])")
P("Output from the custom queue's same operation: `['A', 'B', 'C']`. The order is independent of the contents of the alert identifiers; it follows insertion order.")

H2('2.6 Comparative decision')
TABLE('Table 1. Structure comparison and representative operations',['Structure','Access / insertion / removal','Strengths','Limitations and SOC use'],[
['Array / dynamic array','Index O(1); search O(n); middle insert/delete O(n)','Compact, cache-friendly, indexed access','Shifting/resizing; useful for bounded histories and batch analytics'],
['Singly linked list','Search/index O(n); head/tail update O(1) with references','Flexible growth; no contiguous block required','Per-node overhead and poor locality; useful as the routine queue backbone'],
['Stack','Push/pop/peek O(1) at top','Natural LIFO undo and call-frame model','Only newest item is directly accessible; analyst-action history'],
['Queue','Enqueue/dequeue O(1) in linked design','FIFO fairness and traceability','Does not prioritise risk; routine alert path'],
['Binary heap priority queue','Peek O(1); add/pop O(log n)','Urgent item selected without sorting all entries','No fast arbitrary search/update; critical/high alert path']
])
P("The design uses structures for different access patterns rather than choosing one “best” structure. The ID dictionary provides average O(1) lookup, the linked queue supports FIFO, the heap supports severity-first selection, and the stack supports LIFO action history. Each structure is hidden behind a small operation set. This separation limits coupling: changing the queue implementation does not require the analyst notification code to understand node pointers or heap indices.")

H1('3. Task 2 — system design and formal ADT specification')
H2('3.1 Event flow and stored information')
P("An event source supplies an identifier, severity, receive time and source label. Ingress validation parses severity, checks the identifier and confirms a timezone-aware received_at. The immutable Alert snapshot is stored in the identifier registry and routed to one pending structure: HIGH/CRITICAL to the priority heap, and lower levels to the routine linked queue. The registry is the current snapshot; queue and heap entries select pending work.")
FIG(1,'SOC event flow','Events pass from heterogeneous sources through validation and the identifier registry, then split into priority and routine scheduling. Both feed one processor. State changes publish lifecycle events to analyst subscribers; the bounded stack tracks the latest analyst actions.')
P("Identifiers are unique within the manager. `_by_id` maps an identifier to the current immutable Alert object, enabling average O(1) retrieval and avoiding a linear scan. `received_at` is not overwritten when processing begins; `updated_at` changes when the state moves to IN_PROGRESS, RESOLVED or DISMISSED. Both timestamps must be timezone-aware to avoid comparing naive local times with UTC times. The benchmark and examples use UTC-aware timestamps so ordering is explicit and reproducible.")
P("Processing checks the priority heap first, otherwise dequeues the oldest routine alert. The registry snapshot becomes IN_PROGRESS and an event is emitted. Later valid transitions replace the snapshot and refresh updated_at. Dismissed queued alerts are skipped when encountered; this lazy cancellation avoids an O(n) queue search but retains a stale node until it reaches the front.")
P("AlertEvent notifications contain event type, alert snapshot and emission time. The manager copies subscribers under its RLock and calls them after releasing it, avoiding arbitrary callbacks inside the critical section. Listener failures are isolated; production delivery would normally use an asynchronous broker/WebSocket gateway and durable audit log.")

H2('3.2 UML class model and encapsulation')
FIG(2,'UML class diagram','The model separates immutable alert/event objects from the coordinator and its three custom data structures. Private fields and public operations show the information-hiding boundary.')
P("The Alert class owns the record's identity, severity, status and timestamps. AlertEvent is a separate immutable notification. AlertManager coordinates the structures and holds `_by_id`, `_routine`, `_priority`, `_analyst_actions`, `_listeners` and `_lock` as private members. LinkedQueue, PriorityAlertQueue and ArrayStack each expose only their valid operations. The diagram is a class-level view of the teaching implementation; it does not imply a database, network service or deployment topology that the code does not contain.")
P("Information hiding is implemented in several ways. Callers do not receive the queue nodes or heap list; fields are prefixed as private implementation details and access is through enqueue/dequeue, add/pop and push/pop methods. Frozen dataclasses prevent mutation of alert snapshots, and state transitions pass through AlertManager rather than arbitrary field assignment. Exceptions make rejected operations observable without returning ambiguous sentinel values. In combination, these decisions protect invariants: unique IDs, capacity limits, valid severity values and legal lifecycle transitions.")
P("Encapsulation lowers the number of places that must understand internal representation. If a future version replaces LinkedQueue with a circular buffer, clients that only use the queue contract should not need to change. If a database-backed repository replaces the in-memory dictionary, the same principle allows the coordinator to continue using a find-by-ID interface. The main advantage is not hiding code for its own sake; it is making the correctness boundary explicit and localising change (Liskov and Zilles, 1974).")

H2('3.3 Imperative ADT specification')
P("An ADT defines observable values and operations independently of representation. The contracts below use Q for the routine sequence, P for priority entries, S for the stack and M for the ID map. A priority rank is (severity, −receive-time, −sequence); the lexicographically greatest entry wins, giving stable ties.")
TABLE('Table 2. Imperative ADT contracts',['Operation','Precondition','Postcondition'],[
['Queue.Create(cap)','cap is positive or unbounded','Q := []; size(Q) = 0'],
['Queue.Enqueue(a)','size(Q) < cap(Q)','Q′ := Q followed by a; size(Q′) = size(Q)+1'],
['Queue.Dequeue()','size(Q) > 0','returns head(Q); Q′ := tail(Q); size decreases by one'],
['Queue.Peek()','size(Q) > 0','returns head(Q); Q is unchanged'],
['Priority.Add(a)','size(P) < cap(P)','P′ := P ∪ {a}; heap invariant holds'],
['Priority.Pop()','size(P) > 0','returns arg max rank(P); removes that entry; heap invariant holds'],
['Stack.Push(x)','size(S) < cap(S)','S′ := S followed by x'],
['Stack.Pop()','size(S) > 0','returns last(S); S′ := prefix(S)'],
['Manager.Add(id, sev, t)','id non-empty and absent; sev valid; registry below cap','creates QUEUED alert; M′[id] = alert; exactly one pending structure receives it'],
['Manager.ProcessNext()','at least one pending item','returns highest-ranked priority alert if P non-empty, else oldest Q item; current snapshot becomes IN_PROGRESS'],
['Manager.UpdateStatus(id, s)','id ∈ keys(M); transition allowed','M′[id].status = s and updated_at is refreshed']
])
P("Queue contracts preserve FIFO; stack contracts preserve LIFO. Priority order is severity descending, receive time ascending, then insertion sequence ascending. Each accepted queued alert is registered and scheduled once. Processing chooses priority work before routine work. These observable rules do not depend on linked-node or heap-array representation.")

H2('3.4 ADTs and object orientation')
P("An imperative ADT is a useful basis for object orientation because it groups a state model with operations that control how the state changes. An object can realise that contract and prevent clients from depending on its representation. The AlertManager and custom structures follow this style: public methods express permitted actions, while private attributes preserve internal invariants. This is consistent with the ADT idea that clients should use a defined interface rather than manipulate the representation directly (Liskov and Zilles, 1974).")
P("However, ADTs alone do not constitute the whole of object-oriented programming. Object orientation may also use subtype relationships, dynamic dispatch, inheritance and polymorphic interfaces. The implementation here does not need a large inheritance hierarchy; composition is simpler because the manager owns and coordinates queue, heap and stack objects. I therefore agree that imperative ADTs provide a strong conceptual foundation for object-oriented design, but they are not a complete definition of every object-oriented mechanism. The benefit is a disciplined boundary, not an assumption that every structure should inherit from a common base class.")

H1('4. Task 3 — implementation, testing and algorithm analysis')
H2('4.1 Implementation logic')
P("The implementation is split into models.py, structures.py, manager.py, sorting.py and graph_algorithms.py. This modular separation keeps domain validation out of pointer manipulation and keeps the coordinator from exposing low-level heap details. Type hints document the intended generic values, and dataclasses reduce boilerplate for value objects. The data structures are intentionally implemented directly so the code demonstrates the algorithms rather than wrapping Python's deque or heapq for the assessed core operations.")
P("The linked queue stores a head pointer, tail pointer, size and optional capacity. Its enqueue operation allocates one node and links it at the tail. Dequeue saves the head value, advances the head, decrements size and clears tail if the queue becomes empty. This makes both operations constant-time because no traversal is needed. The structure has O(n) space for n nodes; the per-node object and pointer overhead is a real cost in a high-volume system.")
CODE("def enqueue(self, value):\n    if self._capacity is not None and self._size >= self._capacity:\n        raise QueueFullError(\"queue capacity reached\")\n    node = _Node(value)\n    if self._tail is None:\n        self._head = self._tail = node\n    else:\n        self._tail.next = node\n        self._tail = node\n    self._size += 1")
P("This extract is from structures.py. The capacity guard runs before allocation. The empty-queue branch sets both head and tail to the new node, while the non-empty branch links after the existing tail. The test `test_linked_queue_is_fifo_and_clears_tail_after_last_dequeue` drains the queue and then enqueues again, verifying the important empty-to-non-empty transition.")
P("The priority structure is a custom binary max-heap stored in a Python list. Each node has a parent at floor((i−1)/2), a left child at 2i+1 and a right child at 2i+2. After insertion, sift-up exchanges the new entry with a lower-ranked parent until the heap invariant is restored. After removal, the last entry replaces the root and sift-down exchanges it with the larger child. Both repairs take O(log n) time because heap height is logarithmic. The root is always the next item to process (Cormen, Leiserson and Rivest, 1990).")
CODE("def _priority_key(alert, sequence):\n    return (int(alert.severity),\n            -alert.received_at.timestamp(), -sequence)\n\ndef pop(self):\n    if not self._heap:\n        raise QueueEmptyError(\"cannot pop from an empty priority queue\")\n    root = self._heap[0].alert\n    last = self._heap.pop()\n    if self._heap:\n        self._heap[0] = last\n        self._sift_down(0)\n    return root")
P("The key encodes the scheduling rule in one comparable tuple. A larger severity is preferred; for equal severities a smaller timestamp produces a larger negative timestamp component; if both match, a smaller insertion sequence wins. The counter also prevents Python from comparing Alert objects if two entries otherwise tie. This preserves stable ordering for simultaneous arrivals, rather than leaving equal-priority order dependent on incidental heap swaps.")
P("The manager validates severity and identifiers before modifying storage. A dictionary supports lookup; a queue or heap records the pending work order. `process_next` chooses from the heap first and the routine queue second, updates the registry with an immutable IN_PROGRESS snapshot and emits an AlertEvent. Status transitions are restricted by an explicit mapping: QUEUED can become IN_PROGRESS or DISMISSED; IN_PROGRESS can become RESOLVED or DISMISSED; terminal states cannot move again. This protects the audit meaning of the lifecycle rather than allowing arbitrary status changes.")
CODE("with self._lock:\n    if not self._priority.is_empty():\n        candidate = self._priority.pop()\n    elif not self._routine.is_empty():\n        candidate = self._routine.dequeue()\n    else:\n        raise QueueEmptyError(\"no queued alerts are available\")\n    updated = replace(candidate, status=AlertStatus.IN_PROGRESS,\n                      updated_at=self._clock())\n    self._by_id[updated.identifier] = updated")
P("The displayed excerpt omits the stale-entry loop and event assembly only to keep the listing focused; the full implementation is in Appendix A. The registry is read while holding the lock, so a dismissed record can be skipped. The event is dispatched after the lock is released. Analyst clients can subscribe to alert_added, alert_processing and alert_status_changed events. This demonstrates in-process notifications, not a production WebSocket or durable messaging service.")

H2('4.2 Error handling, correctness and TDD')
P("Tests were written before production code. The initial RED run failed at collection because the expected soc_alerts modules were absent (results/tdd-red.txt). The first GREEN run passed 18 tests; six more checks were added for heap peek, dismissed entries, invalid actions, action-stack overflow, concurrent ingestion and algorithm edge cases. The current suite has 24 passing tests, preserving the red–green sequence (pytest development team, 2026).")
P("Error handling uses named exceptions instead of sentinel values. QueueEmptyError and StackEmptyError distinguish invalid removal from a valid empty value; QueueFullError and StackOverflowError report configured capacity; DuplicateAlertError blocks ambiguous identifiers; InvalidSeverityError rejects unknown severity names; AlertNotFoundError identifies absent records; and InvalidStatusTransitionError prevents illegal lifecycle changes. Alert construction rejects empty IDs and naive timestamps. These failures are important in a SOC because silently dropping an event or accepting an ambiguous identifier can damage traceability and response priority.")
P("Observer exceptions are caught individually and added to listener_errors. This is deliberate fault isolation: a failed subscriber should not cancel a successfully stored record or prevent the next subscriber from receiving an event. The manager does not yet impose a retention limit on its diagnostic error list, so a production service should send those errors to a bounded logging pipeline. Similarly, capacity errors are exposed to the caller; a production ingress layer would need a retry/back-pressure policy rather than assuming that an alert has been accepted when the capacity limit has been reached.")
TABLE('Table 3. Test coverage and evidence',['Area','Cases exercised','Observed result'],[
['Queue and stack','FIFO, LIFO, peek, empty removal, capacity, empty-to-non-empty reset','Pass'],
['Priority heap','Severity order, timestamp tie-break, insertion stability, peek, empty and full','Pass'],
['Manager','IDs, severity validation, capacity, state transitions, timestamps, dismissed pending item','Pass'],
['Real-time observer','Add/process/update notifications and one listener failure','Pass'],
['Concurrency','50 unique alerts submitted through 8 worker threads','Pass'],
['Algorithms','Sorting stability; shortest paths; negative edge/cycle; unorderable graph nodes','Pass']
])
P("The concurrency test checks unique-ID ingestion, not distributed throughput or race behaviour. RLock serialises manager state changes within one process; it does not provide cross-process coordination, durable transactions or delivery guarantees.")

H2('4.3 Time and space complexity of implemented operations')
TABLE('Table 4. Big-O summary for the implementation',['Algorithm / operation','Time complexity','Auxiliary space / storage'],[
['LinkedQueue.enqueue / dequeue / peek','O(1) each','O(1) per operation; O(n) queue storage'],
['ArrayStack.push / pop / peek','O(1) each','O(1) per operation; O(C) preallocated slots'],
['Binary heap add / pop / peek','O(log n) / O(log n) / O(1)','O(1) repair workspace; O(n) heap storage'],
['Dictionary ID lookup','O(1) average; O(n) worst','O(n) registry storage'],
['AlertManager.add_alert','O(1) routine; O(log n) priority, plus O(L) observer callbacks','O(1) record/structure entry plus listener/event data'],
['process_next','O(1) routine or O(log n) priority; stale entries may add skipped work','O(1) per transition; O(k) across k stale entries until drained'],
['update_status / get_alert','O(1) average lookup/update; notification is O(L)','O(1) replacement snapshot; O(L) listener copy'],
['insertion_sort','O(n²) worst/average; O(n) best on sorted input','O(1) auxiliary'],
['merge_sort','O(n log n)','O(n) auxiliary'],
['Dijkstra (lazy heap)','O((V+E) log V) for a simple sparse graph','O(V+E) including graph and frontier'],
['Bellman–Ford','O(VE)','O(V+E) with edge list and distances']
])
P("Here n is queued items, C stack capacity, L listeners, V vertices and E edges. Dijkstra uses a lazy min-heap with duplicate distance entries; for a simple graph its time bound is O((V+E) log V) and frontier storage O(E). Bellman–Ford stores O(E) edges and O(V) distances. Dictionary bounds are average-case (Cormen, Leiserson and Rivest, 1990; Heineman, Pollice and Selkow, 2009).")

H1('5. Task 4 — empirical evaluation and alternatives')
H2('5.1 Measurement design')
P("Three methods were used: asymptotic analysis; median timing across five runs with `time.perf_counter_ns`; and peak traced allocations with `tracemalloc` at 5,000 elements. Timing reflects this host/runtime, while traced memory is not total process RSS (Python Software Foundation, 2024c; 2024d; Leiss, 2007).")
P("The benchmark ran on Python 3.12.3 on a Linux x86_64 VPS reporting one logical CPU, with random seed 1904. Queue and priority timings include building and draining the structures; sort timings include necessary input copies. Results are host-specific: interpreter version, allocator, load and input distribution affect the observed time.")
TABLE('Table 5. FIFO cycle timings (median milliseconds, five runs)',['n','Custom linked queue','Python list with pop(0)'],[
['250','0.0824','0.0225'],['1,000','0.3526','0.0925'],['4,000','1.4234','0.9250'],['16,000','6.0389','15.2750']
])
TABLE('Table 6. Priority cycle timings (median milliseconds, five runs)',['n','Custom binary heap','Sorted list with bisect insertion'],[
['250','0.5712','0.2286'],['1,000','3.0728','0.9720'],['4,000','16.2752','5.5549'],['16,000','91.6699','52.1700']
])
TABLE('Table 7. Sorting timings (median milliseconds, five runs)',['n','Insertion sort','Merge sort'],[
['100','0.1894','0.1157'],['500','5.2688','0.6451'],['1,500','54.0763','2.6409']
])
P("The FIFO and priority tests use n = 250, 1,000, 4,000 and 16,000; sorting uses n = 100, 500 and 1,500. Appendix C contains the machine metadata, individual CSV files and full JSON output. Appendix D preserves the diagram-generation script, PNG/SVG figures and accessible descriptions; Appendix E contains the complete requirements checklist. The complete source files are indexed in Appendix A, and Appendix B contains test, compilation and execution evidence.")

H2('5.2 FIFO: linked queue versus Python list')
FIG(3,'FIFO end-to-end timing','Log-scale comparison of measured queue build-and-drain time for the custom linked queue and Python list front removal.')
P("At 250 items the list cycle is faster (0.0225 ms against 0.0824 ms), and the linked queue remains slower at 1,000 and 4,000 items. At 16,000 items the result reverses: the linked queue takes 6.0389 ms while the list takes 15.2750 ms. The crossover is consistent with the list's O(n) front removal causing repeated element shifts and an O(n²) full drain, while the linked queue performs one constant-time pointer update per removal. It also illustrates why measuring small data sets alone could lead to the wrong structural conclusion.")
P("The list is faster at modest sizes because C-level operations have lower constants than custom Python nodes. At larger n, repeated shifts dominate. Memory matters too: at 5,000 values the list peaks at 191,952 bytes and the linked queue at 391,992 bytes. A production system should also benchmark a circular array queue, which can retain O(1) dequeue with better locality.")

H2('5.3 Priority scheduling: heap versus sorted list')
FIG(4,'Priority queue timing','Measured add-all/remove-all cycle comparing a custom binary max-heap with a dynamically maintained sorted list using bisect insertion.')
P("Heap insertion/removal are O(log n), or O(n log n) for a full cycle. A bisect-maintained sorted list has O(log n) search but O(n) insertion shifts, giving O(n²) total insertion work. Yet it is faster in these runs: 0.2286 vs 0.5712 ms at 250 and 52.17 vs 91.67 ms at 16,000. C-level bisect/list operations have lower constants than Python sift loops.")
P("The result does not prove that a sorted list scales better. At a much larger or more heavily updated queue, quadratic shifting should become increasingly expensive; alternatively, a native heap implementation may reduce the constant factor. The custom heap remains the defensible structure for the stated priority ADT because it gives logarithmic insertion/removal, a predictable root selection rule and bounded repair work. If the actual production workload has low queue sizes and very few insertions, a sorted list could be competitive, but it should be selected only after a representative benchmark and a clear update-cost model.")

H2('5.4 Sorting algorithms')
FIG(5,'Sorting algorithm timing','Measured stable insertion sort versus iterative merge sort for the seeded random arrays at three sizes.')
P("Insertion sort measured 0.1894, 5.2688 and 54.0763 ms at n = 100, 500 and 1,500; merge sort measured 0.1157, 0.6451 and 2.6409 ms. Insertion sort is O(n²) average/worst, while iterative merge sort is O(n log n) time and O(n) extra space. Both are stable (Sedgewick, 1983; Cormen, Leiserson and Rivest, 1990).")
P("Insertion sort remains useful for very small or nearly sorted arrays because it has low setup cost, good locality and O(n) best-case behaviour when the input is already ordered. Merge sort is a better general choice for larger unsorted batches where predictable O(n log n) performance outweighs the extra memory. The SOC scheduling path does not sort the entire queue on every alert; the heap is preferable for incremental priority insertion and removal. Sorting is included to demonstrate comparative analysis and could be useful for offline reporting or exporting a time-window snapshot.")

H2('5.5 Memory results and interpretation')
FIG(6,'Peak traced allocations','Peak tracemalloc bytes for one list and one custom linked queue containing 5,000 integer values.')
P("The recorded peak traced allocations are 191,952 bytes for the Python list and 391,992 bytes for the linked queue. This measurement includes the values and container/node allocations observed by tracemalloc; it excludes process memory not tracked by Python's allocator and should not be read as total resident set size. The difference follows from each linked queue element requiring a node object and a next reference. Tracemalloc is appropriate for comparing these Python allocation paths, but an operating-system RSS measurement and a production load test would be needed to estimate deployment memory more completely (Python Software Foundation, 2024d).")

H2('5.6 Network shortest-path algorithms')
P("The Pearson distinction criterion also asks for two shortest-path algorithms illustrated with examples. A SOC network can be modelled as a weighted directed graph: vertices represent sensors, gateways, switches and servers, and edge weights represent a simplified traversal cost or latency. Figure 7 contains a four-vertex example. From Sensor to Server, the candidate route through Gateway then Switch costs 2 + 1 + 5 = 8; the direct Gateway-to-Server alternative costs 2 + 8 = 10, and the Sensor-to-Switch route costs 4 + 5 = 9. Both implemented algorithms return 8 on this non-negative graph.")
FIG(7,'Weighted SOC network shortest path','Illustrative positive-weight network. The highlighted route is Sensor → Gateway → Switch → Server and costs 8. The same graph is supplied to both algorithms.')
P("Dijkstra's algorithm repeatedly finalises the lowest-distance vertex and relaxes its outgoing edges. With an adjacency list and a binary min-heap, its common sparse-graph bound is O((V+E) log V); the implementation uses lazy duplicate heap entries and checks stale distances when they are removed. Its precondition is non-negative edge weights. A negative edge can invalidate the greedy finalisation argument, so the implementation rejects negative weights instead of returning a plausible but incorrect route (Dijkstra, 1959).")
P("Bellman–Ford relaxes all edges up to V−1 times and uses a final pass to detect reachable negative cycles. Its O(VE) time is slower on large sparse positive-weight graphs, but it supports negative edges (Bellman, 1958). The implementation validates endpoints and stops early when a pass makes no change. Dijkstra suits non-negative SOC network costs; Bellman–Ford is the more general diagnostic.")

H2('5.7 Trade-offs and three benefits of implementation independence')
P("A key ADT trade-off is the balance between representation cost and operation guarantees. A linked queue uses additional memory to make tail insertion and head removal O(1); a circular array queue can be more compact but has a fixed or resizing capacity policy. An array stack is simple and fast but needs a capacity bound; a linked stack grows dynamically but allocates nodes. A binary heap selects urgent work efficiently, but locating and reprioritising an arbitrary alert is not O(1): a production design would need an ID-to-heap-index map or lazy invalidation/version tokens. Making those trade-offs explicit is part of specifying the ADT rather than an afterthought (Leiss, 2007; Heineman, Pollice and Selkow, 2009).")
P("Implementation independence enables substitution (for example, linked queue to ring buffer), optimisation/portability without rewriting clients, and reusable contract tests across alternative implementations. It also localises invariants and reduces coupling between the SOC UI, scheduler and storage.")

H1('6. Security, reliability and operational limitations')
P("The prototype enforces basic data integrity: unique non-empty IDs, enumerated severity, timezone-aware timestamps, explicit lifecycle transitions and capacity bounds. Those controls prevent several classes of accidental corruption, but they do not provide authentication, authorisation, encryption, input provenance verification or durable audit retention. A real SOC would need authenticated event sources, schema validation, tenant separation, access control by analyst role, tamper-evident audit records and a defined retention policy. The current source field is descriptive metadata, not cryptographic proof that an event came from a trusted sensor.")
P("The dictionary and queues are process-local. A restart loses pending work; multiple service instances do not share priority order. RLock is not a distributed lock or transaction coordinator, and callbacks are not durably retried. These limits suit the assignment scope but must be addressed before deployment.")
P("The next step is a durable event log and transactional repository. An asynchronous bus could deliver analyst updates with acknowledgements, bounded retries and dead-letter handling. Horizontal scaling would require a shared broker or partitioned scheduler with explicit ordering semantics. Metrics should include queue depth, oldest-event age, severity latency, rejected capacity events and delivery failures; load tests should cover sustained rates and burst recovery.")
P("Strict priority can starve routine work during a sustained incident flood. It is implemented because the assignment requires high-severity precedence. A production scheduler may add ageing, weighted fairness or a maximum priority burst, but that changes the ADT selection contract and must be agreed and tested explicitly.")

H1('7. Conclusion and recommendations')
P("The backend meets the SOC scenario's two ordering requirements with separate ADTs. A linked FIFO queue retains routine arrival order; a custom binary max-heap selects HIGH/CRITICAL alerts first and resolves ties by earliest timestamp and stable insertion order. An array stack records analyst actions in LIFO order. An ID dictionary supports retrieval, immutable snapshots protect records, and observer events provide in-process updates.")
P("The 24 tests cover normal and error cases, stability, state transitions, capacity and concurrent ingestion. At n = 16,000 the linked queue beats list front-removal but uses more traced memory. The heap has better asymptotic growth than the sorted list, although the latter is faster in this Python run; merge sort scales better than insertion sort. These results show why Big-O, timing and memory must be read together.")
P("For the assignment scenario, the selected structures are justified by their operation contracts and ordering guarantees. For production, the recommendation is to preserve those interfaces while adding durable storage, asynchronous analyst delivery, workload-specific benchmarking, admission/back-pressure controls, metrics and a starvation policy. The ADT boundary makes those improvements possible without exposing every consumer to the internal representation. The project therefore meets the core brief as a tested teaching backend while making its operational limits explicit.")

# Front matter, references and appendix blocks are handled separately.
REFERENCES = [
"Bellman, R. (1958) ‘On a routing problem’, Quarterly of Applied Mathematics, 16, pp. 87–90. https://doi.org/10.1090/qam/102435.",
"Cormen, T.H., Leiserson, C.E. and Rivest, R.L. (1990) Introduction to Algorithms. Cambridge, MA: The MIT Press. ISBN 0-262-03141-8.",
"Dijkstra, E.W. (1959) ‘A note on two problems in connexion with graphs’, Numerische Mathematik, 1, pp. 269–271. https://doi.org/10.1007/BF01386390.",
"Heineman, G.T., Pollice, G. and Selkow, S. (2009) Algorithms in a Nutshell. Sebastopol, CA: O’Reilly Media. ISBN 978-0-596-51624-6. (O’Reilly’s catalogue lists October 2008; the book copyright is 2009.)",
"Leiss, E.L. (2007) A Programmer’s Companion to Algorithm Analysis. Boca Raton, FL: Chapman & Hall/CRC. ISBN 978-1-58488-673-0.",
"Liskov, B. and Zilles, S.N. (1974) ‘Programming with abstract data types’, Proceedings of the ACM SIGPLAN Symposium on Very High Level Languages, pp. 50–59. https://doi.org/10.1145/800233.807045.",
"Pearson (2024) Unit 19: Data Structures & Algorithms — Assignment Brief. Effective assignment design for Higher Nationals in Computing/Computing for England, Issue 2, July 2024, pp. 1–7. (Supplied assignment brief.)",
"Python Software Foundation (2024a) ‘dataclasses — Data Classes’, Python 3.12 documentation. Available at: https://docs.python.org/3.12/library/dataclasses.html (Accessed: 22 November 2026).",
"Python Software Foundation (2024b) ‘threading — Thread-based parallelism’, Python 3.12 documentation. Available at: https://docs.python.org/3.12/library/threading.html (Accessed: 22 November 2026).",
"Python Software Foundation (2024c) ‘time — Time access and conversions’, Python 3.12 documentation. Available at: https://docs.python.org/3.12/library/time.html (Accessed: 22 November 2026).",
"Python Software Foundation (2024d) ‘tracemalloc — Trace memory allocations’, Python 3.12 documentation. Available at: https://docs.python.org/3.12/library/tracemalloc.html (Accessed: 22 November 2026).",
"pytest development team (2026) ‘Get Started’, pytest documentation. Available at: https://docs.pytest.org/en/stable/getting-started.html (Accessed: 22 November 2026).",
"Sedgewick, R. (1983) Algorithms. Reading, MA: Addison-Wesley. ISBN 0-201-06672-6.",
"Wirth, N. (2004) Algorithms and Data Structures. Oberon version. Zürich: ETH Zürich. Available at: https://people.inf.ethz.ch/wirth/AD.pdf (Accessed: 22 November 2026)."
]

# Pull short snippets and complete source files into a structured appendix directory.
APP = ROOT/'appendices'
SRCAPP = APP/'source-code'
SRCAPP.mkdir(parents=True, exist_ok=True)
for path in sorted((ROOT/'src/soc_alerts').glob('*.py')):
    shutil.copy2(path, SRCAPP/path.name)
(APP/'source-code-index.md').write_text('# Appendix A — Complete source code\n\nThe complete, commented Python source files are included in `source-code/` and mirror the tested files under `src/soc_alerts/`. Run `PYTHONPATH=src python3 -m soc_alerts.demo` from the project root to reproduce the example output.\n\nFiles: ' + ', '.join(p.name for p in sorted(SRCAPP.glob('*.py'))) + '.\n')
(APP/'B-test-evidence.md').write_text('# Appendix B — Test and execution evidence\n\n- Initial RED test-first run: `results/tdd-red.txt` (collection failed because production modules did not yet exist).\n- First GREEN run: `results/pytest-first-green.txt`.\n- Refined suite run: `results/pytest-refined-green.txt`.\n- Reproducible demo output: `results/demo-output.txt`.\n- Compilation command: `python3 -m compileall -q src tests benchmarks`.\n- Independent final verification logs are captured separately in `results/`.\n')
(APP/'C-benchmark-evidence.md').write_text('# Appendix C — Benchmark evidence\n\nThe raw output from the reproducible benchmark is stored in `results/benchmark-results.json` and the three corresponding CSV files. The exact benchmark implementation is `benchmarks/benchmark.py`. It uses deterministic input generation, `perf_counter_ns`, five repetitions and median summaries, plus `tracemalloc` peak allocation measurement.\n')
(APP/'D-figures-and-diagrams.md').write_text('# Appendix D — Diagram and chart source\n\nFigure source is in `diagrams/create_figures.py`; rendered high-resolution PNG and scalable SVG figures are stored in `diagrams/`. The textual figure register and alternative descriptions are in `docs/figure-register.md`.\n')

# Count narrative body words, excluding front matter, references and appendices.
word_parts=[]
for block in B:
    if block[0] in ('h1','h2','p'): word_parts.append(block[1])
    elif block[0]=='bullets': word_parts.extend(block[1])
    elif block[0]=='table':
        word_parts.append(block[1]); word_parts.extend(block[2])
        for row in block[3]: word_parts.extend(row)
body_text=' '.join(word_parts)
word_count=len(re.findall(r"\b[\w’'-]+\b",body_text))
if not 4000 <= word_count <= 5500:
    raise SystemExit(f'Main report word count {word_count} is outside 4,000-5,500; extend or trim content.')

# ---------- DOCX ----------
doc=Document(); sec=doc.sections[0]
sec.top_margin=Inches(.78); sec.bottom_margin=Inches(.72); sec.left_margin=Inches(.82); sec.right_margin=Inches(.82)
sec.header_distance=Inches(.35); sec.footer_distance=Inches(.35)
styles=doc.styles
for name in ['Normal','Body Text']:
    st=styles[name]; st.font.name='Lato'; st.font.size=Pt(10.4); st.font.color.rgb=RGBColor.from_string(NAVY)
    st.paragraph_format.space_after=Pt(6); st.paragraph_format.line_spacing=1.15
for name,size,color in [('Title',31,NAVY),('Subtitle',14,SLATE),('Heading 1',18,NAVY),('Heading 2',13,TEAL),('Heading 3',11,INK)]:
    st=styles[name]; st.font.name='Lato'; st.font.size=Pt(size); st.font.bold=name!='Subtitle'; st.font.color.rgb=RGBColor.from_string(color)
    st.paragraph_format.space_before=Pt(14 if 'Heading' in name else 0); st.paragraph_format.space_after=Pt(6)
    st.paragraph_format.keep_with_next=True
if 'Code Block' not in styles:
    st=styles.add_style('Code Block',1)
else: st=styles['Code Block']
st.font.name='DejaVu Sans Mono'; st.font.size=Pt(8); st.font.color.rgb=RGBColor.from_string('203244')
st.paragraph_format.left_indent=Inches(.15); st.paragraph_format.right_indent=Inches(.1); st.paragraph_format.space_before=Pt(3); st.paragraph_format.space_after=Pt(7); st.paragraph_format.line_spacing=1.0
if 'Caption Custom' not in styles: cap=styles.add_style('Caption Custom',1)
else: cap=styles['Caption Custom']
cap.font.name='Lato'; cap.font.size=Pt(8.6); cap.font.italic=True; cap.font.color.rgb=RGBColor.from_string(SLATE)
cap.paragraph_format.space_after=Pt(10); cap.paragraph_format.keep_with_next=True
# Header and page-number footer.
header=sec.header.paragraphs[0]; header.text='UNIT 19  /  DATA STRUCTURES & ALGORITHMS                                              SOC ALERT MANAGEMENT'
header.style='Caption Custom'
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=footer.add_run('TECHNICAL REPORT  •  '); r.font.name='Lato'; r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string(SLATE)
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)
# Set update fields on open.
settings=doc.settings._element; update=OxmlElement('w:updateFields'); update.set(qn('w:val'),'true'); settings.append(update)
# Cover.
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(76)
r=p.add_run('UNIT 19'); r.font.name='Lato'; r.font.size=Pt(15); r.font.bold=True; r.font.color.rgb=RGBColor.from_string(TEAL)
p=doc.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(22); p.add_run('Data Structures\n& Algorithms')
p=doc.add_paragraph(style='Subtitle'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('SOC Alert Management Backend')
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(22)
r=p.add_run('WRITTEN TECHNICAL REPORT'); r.font.name='Lato'; r.font.bold=True; r.font.size=Pt(10); r.font.color.rgb=RGBColor.from_string(TEAL)
for text in ['Student name: [INSERT STUDENT NAME]','Student ID: [INSERT STUDENT ID]','Unit tutor: [INSERT TUTOR NAME]','Assignment title: [INSERT ASSIGNMENT TITLE]','Academic year: 2026','Unit: Pearson Higher National Computing — Unit 19']:
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(7); p.add_run(text)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(50)
r=p.add_run('Submission format: DOCX and PDF  |  Referencing: Harvard'); r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string(SLATE)
doc.add_page_break()
# Contents (static navigation list; page references match the rendered DOCX/PDF pagination)
doc.add_heading('Contents',0)
contents=[
('Executive summary','3'),('Assessment coverage map','3'),
('1. Introduction and requirements interpretation','4'),
('2. Task 1 — analysis and selection of data structures','4'),
('   2.1–2.3 Data types, arrays and linked lists','4'),('   2.4–2.6 Stacks, queues and comparison','5'),
('3. Task 2 — system design and formal ADT specification','6'),
('   3.1 Event flow and stored information','6'),('   3.2 UML class model and encapsulation','7'),
('   3.3 Imperative ADT specification','8'),('   3.4 ADTs and object orientation','8'),
('4. Task 3 — implementation, testing and algorithm analysis','9'),
('   4.1 Implementation logic','9'),('   4.2 Error handling and TDD','10'),('   4.3 Complexity analysis','11'),
('5. Task 4 — empirical evaluation and alternatives','11'),
('   5.1 Measurement design','11'),('   5.2 FIFO comparison','12'),('   5.3 Priority comparison','13'),
('   5.4 Sorting algorithms','14'),('   5.5 Memory results and 5.6 Shortest paths','15'),('   5.7 Trade-offs','16'),
('6. Security, reliability and operational limitations','17'),('7. Conclusion and recommendations','17'),
('References','17'),('Appendices A–E','18–19')]
for label,page in contents:
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(3); p.paragraph_format.tab_stops.add_tab_stop(Inches(6.25))
    r=p.add_run(label+'\t'+page); r.font.name='Lato'; r.font.size=Pt(9); r.font.color.rgb=RGBColor.from_string(NAVY)
doc.add_page_break()
# Overview / abstract.
doc.add_heading('Executive summary',0)
for para in [
"This report presents a tested Python backend for a Security Operations Centre alert queue. It separates routine FIFO work from HIGH/CRITICAL priority work, uses an array-backed LIFO action stack, indexes current records by identifier, and publishes immutable lifecycle events to subscribed analysts.",
"The implementation includes 24 tests, explicit capacity and validation errors, stable heap tie-breaking by severity and receive time, and two educational sorting and two shortest-path algorithms. Actual performance measurements and memory allocations are reported alongside Big-O analysis. The measured results show why implementation constants and memory overhead must be considered with asymptotic growth.",
"The prototype is intentionally in-memory and single-process. It demonstrates the assignment's backend logic, not a production-ready SOC platform; durable persistence, asynchronous delivery, authentication and distributed scheduling are recommended next steps."]:
    doc.add_paragraph(para)
# Requirements alignment table.
doc.add_heading('Assessment coverage map',1)
rows=[['LO1','Arrays, linked lists, stacks, queues; FIFO/LIFO; function-call stack; sorting and shortest paths','Sections 2 and 5'],['LO2','Formal queue, priority and stack contracts; information hiding; ADT/OOP discussion','Section 3'],['LO3','Custom structures, alert manager, error handling, tests and source evidence','Section 4 and Appendices A–B'],['LO4','Big-O, scaling timing, memory profiling, alternative comparisons and trade-offs','Section 5']]
t=doc.add_table(rows=1, cols=3); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'
for i,val in enumerate(['Outcome','Evidence','Location']): t.rows[0].cells[i].text=val
for row in rows:
    cells=t.add_row().cells
    for i,val in enumerate(row): cells[i].text=val
for row in t.rows:
    for i,c in enumerate(row.cells):
        c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for p in c.paragraphs:
            p.paragraph_format.space_after=Pt(2)
            for run in p.runs: run.font.name='Lato'; run.font.size=Pt(8.5)
        if row==t.rows[0]:
            tcPr=c._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),NAVY); tcPr.append(shd)
            for p in c.paragraphs:
                for run in p.runs: run.font.bold=True; run.font.color.rgb=RGBColor(255,255,255)
# Add content blocks.
for block in B:
    kind=block[0]
    if kind=='h1': doc.add_heading(block[1],1)
    elif kind=='h2': doc.add_heading(block[1],2)
    elif kind=='p': doc.add_paragraph(block[1])
    elif kind=='bullets':
        for item in block[1]: doc.add_paragraph(item,style='List Bullet')
    elif kind=='code':
        p=doc.add_paragraph(style='Code Block'); p.paragraph_format.keep_together=True
        pPr=p._p.get_or_add_pPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'F0F4F6'); pPr.append(shd)
        p.add_run(block[1])
    elif kind=='table':
        _,caption,headers,rows,widths=block
        p=doc.add_paragraph(style='Caption Custom'); p.add_run(caption)
        table=doc.add_table(rows=1,cols=len(headers)); table.style='Table Grid'; table.alignment=WD_TABLE_ALIGNMENT.CENTER
        for i,v in enumerate(headers): table.rows[0].cells[i].text=v
        for rowdata in rows:
            cells=table.add_row().cells
            for i,v in enumerate(rowdata): cells[i].text=str(v)
        for ri,row in enumerate(table.rows):
            for c in row.cells:
                c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for pp in c.paragraphs:
                    pp.paragraph_format.space_after=Pt(2); pp.paragraph_format.line_spacing=1.02
                    for rr in pp.runs: rr.font.name='Lato'; rr.font.size=Pt(7.8)
                if ri==0:
                    tcPr=c._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),NAVY); tcPr.append(shd)
                    for pp in c.paragraphs:
                        for rr in pp.runs: rr.font.bold=True; rr.font.color.rgb=RGBColor(255,255,255)
                elif ri%2==0:
                    tcPr=c._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),'F3F7F9'); tcPr.append(shd)
        doc.add_paragraph()
    elif kind=='figure':
        _,num,caption,desc,width=block
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before=Pt(5); p.paragraph_format.space_after=Pt(2)
        images={1:'figure-01-soc-data-flow.png',2:'figure-02-uml-class-diagram.png',3:'figure-03-fifo-scaling.png',4:'figure-04-priority-scaling.png',5:'figure-05-sorting-scaling.png',6:'figure-06-memory-profile.png',7:'figure-07-shortest-path-example.png'}
        p.add_run().add_picture(str(ROOT/'diagrams'/images[num]),width=Inches(width))
        cp=doc.add_paragraph(style='Caption Custom'); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER; cp.add_run(f'Figure {num}. {caption}')
        al=doc.add_paragraph(desc); al.style='Caption Custom'
    elif kind=='pagebreak': doc.add_page_break()
# References.
doc.add_heading('References',0)
for ref in REFERENCES:
    p=doc.add_paragraph(ref); p.paragraph_format.left_indent=Inches(.25); p.paragraph_format.first_line_indent=Inches(-.25); p.paragraph_format.space_after=Pt(7)
# Appendices.
doc.add_heading('Appendices',0)
doc.add_heading('Appendix A — Full source code',1)
doc.add_paragraph('The complete fully commented Python source files are supplied as separate files under appendices/source-code/. They mirror the tested implementation under src/soc_alerts/. The source-code index identifies every file. The files are included separately to preserve readable, searchable code rather than shrinking long listings to an unreadable size in this report.')
for name,desc in [('models.py','Alert and AlertEvent immutable domain records, severity enumeration and status values.'),('structures.py','Custom linked FIFO queue, fixed-capacity array stack and binary max-heap priority queue.'),('manager.py','Thread-safe alert coordinator, ID registry, state transitions and observer notifications.'),('sorting.py','Stable insertion sort and iterative stable merge sort.'),('graph_algorithms.py','Dijkstra and Bellman–Ford shortest-path algorithms with validation.'),('demo.py','Reproducible command-line demonstration and sample output.')]:
    doc.add_paragraph(f'{name} — {desc}',style='List Bullet')
doc.add_paragraph('The project also includes benchmarks/benchmark.py, which regenerates the performance data used by the figures and tables.')
doc.add_heading('Appendix B — Test and execution evidence',1)
doc.add_paragraph('Test-first RED evidence is preserved in results/tdd-red.txt. Green and refinement runs are in results/pytest-first-green.txt and results/pytest-refined-green.txt. The reproducible output is results/demo-output.txt. The final compile and independent test logs are listed in the project README and stored in results/.')
doc.add_heading('Appendix C — Empirical benchmark files',1)
doc.add_paragraph('The full machine metadata and raw medians are stored in results/benchmark-results.json. Individual timing rows are also supplied as results/fifo_scaling.csv, results/priority_scaling.csv and results/sorting_scaling.csv. Run python3 benchmarks/benchmark.py to regenerate them.')
doc.add_heading('Appendix D — Diagram sources and visual descriptions',1)
doc.add_paragraph('The figure-generation script is diagrams/create_figures.py. Each figure is supplied as a high-resolution PNG for Word/PowerPoint and a vector SVG for scalable reuse. Descriptions and source notes are documented in docs/figure-register.md.')
doc.add_heading('Appendix E — Requirements checklist',1)
doc.add_paragraph('The complete task, learning-outcome and Pass/Merit/Distinction checklist is docs/requirements-checklist.md. The final status of each item is updated after the final independent verification pass.')
doc.core_properties.title='Unit 19 Data Structures & Algorithms — SOC Alert Management Backend'
doc.core_properties.subject='Pearson HND Computing Unit 19 technical report'
doc.core_properties.author='[STUDENT NAME]'
doc.core_properties.keywords='SOC, alerts, FIFO, LIFO, priority queue, data structures, algorithms'
OUTDOC=ROOT/'report'/'Unit19_DSA_SOC_Alerts_Technical_Report.docx'; doc.save(OUTDOC)

# ---------- PDF (same content model; paginated contents and page furniture) ----------
# Register available Lato fonts for a readable, consistent PDF.
fontdir=Path('/usr/share/fonts/truetype/lato')
for nm,file in [('Lato','Lato-Regular.ttf'),('Lato-Bold','Lato-Bold.ttf'),('Lato-Italic','Lato-Italic.ttf')]:
    f=fontdir/file
    if f.exists(): pdfmetrics.registerFont(TTFont(nm,str(f)))
mono=Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
if mono.exists(): pdfmetrics.registerFont(TTFont('DejaVuMono',str(mono)))
ss=getSampleStyleSheet()
ss.add(ParagraphStyle('BodyX',parent=ss['BodyText'],fontName='Lato',fontSize=9,leading=13,textColor=colors.HexColor('#'+NAVY),spaceAfter=7,alignment=TA_LEFT))
ss.add(ParagraphStyle('H1X',parent=ss['Heading1'],fontName='Lato-Bold',fontSize=17,leading=21,textColor=colors.HexColor('#'+NAVY),spaceBefore=15,spaceAfter=8,keepWithNext=True))
ss.add(ParagraphStyle('H2X',parent=ss['Heading2'],fontName='Lato-Bold',fontSize=12.5,leading=16,textColor=colors.HexColor('#'+TEAL),spaceBefore=11,spaceAfter=6,keepWithNext=True))
ss.add(ParagraphStyle('TitleX',parent=ss['Title'],fontName='Lato-Bold',fontSize=29,leading=34,textColor=colors.HexColor('#'+NAVY),alignment=TA_CENTER))
ss.add(ParagraphStyle('SubX',parent=ss['Normal'],fontName='Lato',fontSize=13,leading=18,textColor=colors.HexColor('#'+SLATE),alignment=TA_CENTER))
ss.add(ParagraphStyle('SmallX',parent=ss['Normal'],fontName='Lato',fontSize=8,leading=10,textColor=colors.HexColor('#'+SLATE),spaceAfter=6))
ss.add(ParagraphStyle('CaptionX',parent=ss['Normal'],fontName='Lato-Italic',fontSize=8,leading=10,textColor=colors.HexColor('#'+SLATE),alignment=TA_CENTER,spaceAfter=8))
ss.add(ParagraphStyle('CellX',parent=ss['Normal'],fontName='Lato',fontSize=7,leading=9,textColor=colors.HexColor('#'+NAVY)))
ss.add(ParagraphStyle('CellHeadX',parent=ss['Normal'],fontName='Lato-Bold',fontSize=7.2,leading=9,textColor=colors.white))
ss.add(ParagraphStyle('CodeX',parent=ss['Code'],fontName='DejaVuMono',fontSize=7,leading=9,textColor=colors.HexColor('#203244'),backColor=colors.HexColor('#F0F4F6'),borderPadding=6,leftIndent=5,rightIndent=5,spaceBefore=4,spaceAfter=8))
ss.add(ParagraphStyle('TOC1X',parent=ss['Normal'],fontName='Lato-Bold',fontSize=8.5,leading=10,leftIndent=0,firstLineIndent=0,spaceBefore=4))
ss.add(ParagraphStyle('TOC2X',parent=ss['Normal'],fontName='Lato',fontSize=7.5,leading=9,leftIndent=14,firstLineIndent=0))

class ReportDoc(BaseDocTemplate):
    def __init__(self,filename,**kw):
        super().__init__(filename,**kw)
        frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,id='normal',leftPadding=0,rightPadding=0,topPadding=5,bottomPadding=5)
        self.addPageTemplates([PageTemplate(id='main',frames=frame,onPage=self.decorate)])
    def decorate(self,canvas,doc):
        if doc.page==1: return
        canvas.saveState(); w,h=A4
        canvas.setStrokeColor(colors.HexColor('#'+LIGHT)); canvas.setLineWidth(.5)
        canvas.line(18*mm,h-15*mm,w-18*mm,h-15*mm)
        canvas.setFont('Lato',7); canvas.setFillColor(colors.HexColor('#'+SLATE))
        canvas.drawString(18*mm,h-11.5*mm,'UNIT 19  /  DATA STRUCTURES & ALGORITHMS')
        canvas.drawRightString(w-18*mm,h-11.5*mm,'SOC ALERT MANAGEMENT')
        canvas.line(18*mm,14*mm,w-18*mm,14*mm)
        canvas.drawCentredString(w/2,9*mm,f'TECHNICAL REPORT  •  {doc.page}')
        canvas.restoreState()
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name in ('H1X','H2X'):
            level=0 if flowable.style.name=='H1X' else 1
            text=flowable.getPlainText()
            key=f'h{level}-{self.page}-{abs(hash(text))%1000000}'
            self.canv.bookmarkPage(key)
            self.notify('TOCEntry',(level,text,self.page,key))

PDF=ROOT/'report'/'Unit19_DSA_SOC_Alerts_Technical_Report.pdf'
pdfdoc=ReportDoc(str(PDF),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=22*mm,bottomMargin=20*mm,title='Unit 19 — SOC Alert Management')
pdfdoc.multiBuild([]) if False else None
story=[]
story += [Spacer(1,34*mm),Paragraph('UNIT 19',ParagraphStyle('UnitX',fontName='Lato-Bold',fontSize=13,textColor=colors.HexColor('#'+TEAL),alignment=TA_CENTER)),Spacer(1,9*mm),Paragraph('Data Structures<br/>&amp; Algorithms',ss['TitleX']),Spacer(1,6*mm),Paragraph('SOC Alert Management Backend',ss['SubX']),Spacer(1,12*mm),Paragraph('<b>WRITTEN TECHNICAL REPORT</b>',ParagraphStyle('TagX',fontName='Lato-Bold',fontSize=9,textColor=colors.HexColor('#'+TEAL),alignment=TA_CENTER)),Spacer(1,12*mm)]
for txt in ['Student name: [INSERT STUDENT NAME]','Student ID: [INSERT STUDENT ID]','Unit tutor: [INSERT TUTOR NAME]','Assignment title: [INSERT ASSIGNMENT TITLE]','Academic year: 2026','Pearson Higher National Computing — Unit 19']:
    story.append(Paragraph(txt,ParagraphStyle('CoverFieldX',fontName='Lato',fontSize=9.5,leading=15,textColor=colors.HexColor('#'+NAVY),alignment=TA_CENTER)))
story += [Spacer(1,22*mm),Paragraph('Submission format: DOCX and PDF  |  Referencing: Harvard',ss['SmallX']),PageBreak(),Paragraph('Contents',ss['H1X'])]
toc=TableOfContents(); toc.levelStyles=[ss['TOC1X'],ss['TOC2X']]; toc.dotsMinLevel=0; story += [toc,PageBreak(),Paragraph('Executive summary',ss['H1X'])]
for para in [
"This report presents a tested Python backend for a Security Operations Centre alert queue. It separates routine FIFO work from HIGH/CRITICAL priority work, uses an array-backed LIFO action stack, indexes current records by identifier, and publishes immutable lifecycle events to subscribed analysts.",
"The implementation includes 24 tests, explicit capacity and validation errors, stable heap tie-breaking by severity and receive time, and two educational sorting and two shortest-path algorithms. Actual performance measurements and memory allocations are reported alongside Big-O analysis. The measured results show why implementation constants and memory overhead must be considered with asymptotic growth.",
"The prototype is intentionally in-memory and single-process. It demonstrates the assignment's backend logic, not a production-ready SOC platform; durable persistence, asynchronous delivery, authentication and distributed scheduling are recommended next steps."]:
    story.append(Paragraph(para,ss['BodyX']))
story += [Paragraph('Assessment coverage map',ss['H2X'])]
def pdf_table(caption,headers,rows,colWidths=None,head=True):
    data=[[Paragraph(str(x),ss['CellHeadX']) for x in headers]]
    for row in rows: data.append([Paragraph(str(x).replace('&','&amp;'),ss['CellX']) for x in row])
    tbl=Table(data,colWidths=colWidths,repeatRows=1,hAlign='LEFT')
    commands=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#'+NAVY)),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#'+LIGHT)),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]
    for i in range(1,len(data)):
        if i%2==0: commands.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#'+PALE)))
    tbl.setStyle(TableStyle(commands))
    return [Paragraph(caption,ss['SmallX']),tbl,Spacer(1,7)] if caption else [tbl,Spacer(1,7)]
story += pdf_table('', ['Outcome','Evidence','Location'],[
['LO1','Arrays, linked lists, stacks, queues; FIFO/LIFO; function-call stack; sorting and shortest paths','Sections 2 and 5'],['LO2','Formal queue, priority and stack contracts; information hiding; ADT/OOP discussion','Section 3'],['LO3','Custom structures, alert manager, error handling, tests and source evidence','Section 4 and Appendices A–B'],['LO4','Big-O, scaling timing, memory profiling, alternatives and trade-offs','Section 5']], [22*mm,110*mm,42*mm])

for block in B:
    kind=block[0]
    if kind=='h1': story.append(Paragraph(block[1],ss['H1X']))
    elif kind=='h2': story.append(Paragraph(block[1],ss['H2X']))
    elif kind=='p': story.append(Paragraph(block[1],ss['BodyX']))
    elif kind=='bullets':
        for item in block[1]: story.append(Paragraph('• '+item,ss['BodyX']))
    elif kind=='code': story.append(Preformatted(block[1],ss['CodeX'],maxLineLength=88))
    elif kind=='table': story += pdf_table(block[1],block[2],block[3])
    elif kind=='figure':
        num,caption,desc,width=block[1:]
        images={1:'figure-01-soc-data-flow.png',2:'figure-02-uml-class-diagram.png',3:'figure-03-fifo-scaling.png',4:'figure-04-priority-scaling.png',5:'figure-05-sorting-scaling.png',6:'figure-06-memory-profile.png',7:'figure-07-shortest-path-example.png'}
        im=Image(str(ROOT/'diagrams'/images[num])); maxw=min(width*25.4*mm/25.4,174*mm); im.drawWidth=maxw; im.drawHeight=maxw*im.imageHeight/im.imageWidth
        story += [im,Paragraph(f'Figure {num}. {caption}',ss['CaptionX']),Paragraph(desc,ss['SmallX'])]
    elif kind=='pagebreak': story.append(PageBreak())

story.append(Paragraph('References',ss['H1X']))
for ref in REFERENCES:
    story.append(Paragraph(ref.replace('&','&amp;'),ss['BodyX']))
story += [Paragraph('Appendices',ss['H1X']),Paragraph('Appendix A — Full source code',ss['H2X']),Paragraph('The complete fully commented Python source files are supplied as separate files under appendices/source-code/. They mirror the tested implementation under src/soc_alerts/. The source-code index identifies every file. The files are separate so their names and indentation remain readable and searchable.',ss['BodyX'])]
for name,desc in [('models.py','Alert and AlertEvent immutable domain records, severity enumeration and status values.'),('structures.py','Custom linked FIFO queue, fixed-capacity array stack and binary max-heap priority queue.'),('manager.py','Thread-safe alert coordinator, ID registry, state transitions and observer notifications.'),('sorting.py','Stable insertion sort and iterative stable merge sort.'),('graph_algorithms.py','Dijkstra and Bellman–Ford shortest-path algorithms with validation.'),('demo.py','Reproducible command-line demonstration and sample output.')]: story.append(Paragraph('• '+name+' — '+desc,ss['BodyX']))
story += [Paragraph('The project also includes benchmarks/benchmark.py, which regenerates the performance data used by the figures and tables.',ss['BodyX']),Paragraph('Appendix B — Test and execution evidence',ss['H2X']),Paragraph('Test-first RED evidence is preserved in results/tdd-red.txt. Green and refinement runs are in results/pytest-first-green.txt and results/pytest-refined-green.txt. The reproducible output is results/demo-output.txt. Final compilation and independent test logs are stored in results/.',ss['BodyX']),Paragraph('Appendix C — Empirical benchmark files',ss['H2X']),Paragraph('The full machine metadata and raw medians are stored in results/benchmark-results.json. Individual timing rows are also supplied as results/fifo_scaling.csv, results/priority_scaling.csv and results/sorting_scaling.csv. Run python3 benchmarks/benchmark.py to regenerate them.',ss['BodyX']),Paragraph('Appendix D — Diagram sources and visual descriptions',ss['H2X']),Paragraph('The figure-generation script is diagrams/create_figures.py. Each figure is supplied as a high-resolution PNG for Word/PowerPoint and a vector SVG for scalable reuse. Descriptions and source notes are documented in docs/figure-register.md.',ss['BodyX']),Paragraph('Appendix E — Requirements checklist',ss['H2X']),Paragraph('The complete task, learning-outcome and Pass/Merit/Distinction checklist is docs/requirements-checklist.md. Its final status is updated after independent verification.',ss['BodyX'])]
pdfdoc.multiBuild(story)

# Machine-readable word count and artifact manifest.
(ROOT/'results'/'report-word-count.json').write_text(json.dumps({'main_body_words':word_count,'count_scope':'sections 1–7, including headings, prose and table text; excludes cover, executive summary, code extracts, references and appendices'},indent=2)+'\n')
print(json.dumps({'docx':str(OUTDOC),'pdf':str(PDF),'main_body_words':word_count,'references':len(REFERENCES),'figures':7},indent=2))
