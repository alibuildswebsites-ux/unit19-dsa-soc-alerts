"""Generate a custom, speaker-noted PowerPoint deck from verified project evidence."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.deps'))
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE

NAVY='18324A'; TEAL='087F8C'; SLATE='627588'; PALE='F3F7F9'; LIGHT='DCE6EB'; AMBER='C58B3D'; WHITE='FFFFFF'; GREEN='3A806C'; RED='B85C52'; INK='22384A'
prs=Presentation(); prs.slide_width= Inches(13.333); prs.slide_height= Inches(7.5)
blank=prs.slide_layouts[6]
W=13.333; H=7.5

def rgb(h): return RGBColor.from_string(h)

def rect(slide,x,y,w,h,fill=WHITE,line=None,radius=True):
    shape=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb=rgb(fill)
    shape.line.color.rgb=rgb(line or fill); shape.line.width=Pt(1)
    if radius:
        try: shape.adjustments[0]=0.12
        except Exception: pass
    return shape

def txt(slide,text,x,y,w,h,size=16,color=NAVY,bold=False,font='Lato',align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, margin=.03):
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=box.text_frame; tf.clear(); tf.word_wrap=True
    tf.margin_left=Inches(margin); tf.margin_right=Inches(margin); tf.margin_top=Inches(margin); tf.margin_bottom=Inches(margin); tf.vertical_anchor=valign
    lines=text.split('\n')
    for i,line in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=line; p.alignment=align; p.space_after=Pt(4)
        for r in p.runs:
            r.font.name=font; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=rgb(color)
    return box

def rich_code(slide, lines, x,y,w,h):
    rect(slide,x,y,w,h,fill='142638',line='142638')
    box=slide.shapes.add_textbox(Inches(x+.20),Inches(y+.14),Inches(w-.4),Inches(h-.28)); tf=box.text_frame; tf.clear(); tf.word_wrap=False
    tf.margin_left=0; tf.margin_right=0; tf.margin_top=0; tf.margin_bottom=0
    for i,line in enumerate(lines.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.space_after=Pt(3)
        # Compact, syntax-inspired colouring by line role; exact source wording retained.
        color='DCE8EE' if not line.lstrip().startswith(('def ','if ','return ','raise ')) else '76D6C4'
        r=p.add_run(); r.text=line; r.font.name='DejaVu Sans Mono'; r.font.size=Pt(12); r.font.color.rgb=rgb(color)

def base(title, section, slide_no, subtitle=None):
    s=prs.slides.add_slide(blank)
    bg=s.background.fill; bg.solid(); bg.fore_color.rgb=rgb('F8FAFB')
    # small top keyline and section marker
    rect(s,.45,.38,.42,.055,fill=TEAL,line=TEAL,radius=False)
    txt(s,section.upper(),.98,.29,5,.25,9,TEAL,True)
    txt(s,title,.48,.68,12.2,.60,25,NAVY,True)
    if subtitle: txt(s,subtitle,.5,1.34,12,.40,11,SLATE)
    rect(s,.48,7.08,12.35,.012,fill=LIGHT,line=LIGHT,radius=False)
    txt(s,'UNIT 19  /  SOC ALERT MANAGEMENT',.5,7.14,5,.18,7,SLATE,True)
    txt(s,f'{slide_no:02d}',12.15,7.12,.55,.2,8,SLATE,True,align=PP_ALIGN.RIGHT)
    return s

def notes(slide,text):
    try: slide.notes_slide.notes_text_frame.text=text
    except Exception: pass

def pill(slide,text,x,y,w,color=TEAL):
    rect(slide,x,y,w,.34,fill=color,line=color,radius=True)
    txt(slide,text,x+.04,y+.045,w-.08,.22,9,WHITE,True,align=PP_ALIGN.CENTER)

def kpi(slide,x,y,w,label,value,accent=TEAL,foot=''):
    rect(slide,x,y,w,1.25,fill=WHITE,line=LIGHT)
    rect(slide,x,y,.06,1.25,fill=accent,line=accent,radius=False)
    txt(slide,label.upper(),x+.18,y+.16,w-.35,.22,8,SLATE,True)
    txt(slide,value,x+.18,y+.43,w-.35,.43,23,NAVY,True)
    if foot: txt(slide,foot,x+.18,y+.91,w-.35,.22,8,SLATE)

def add_image(slide,filename,x,y,w,h):
    path=ROOT/'diagrams'/filename
    slide.shapes.add_picture(str(path),Inches(x),Inches(y),width=Inches(w),height=Inches(h))

# Slide 1 - cover
s=prs.slides.add_slide(blank); s.background.fill.solid(); s.background.fill.fore_color.rgb=rgb(NAVY)
rect(s,9.0,0.0,4.35,7.5,fill='102638',line='102638',radius=False)
for i,(col,hh) in enumerate([(TEAL,1.2),(AMBER,.8),(GREEN,1.5)]):
    rect(s,9.55+i*1.0,4.4-hh,0.62,hh,fill=col,line=col,radius=True)
    txt(s,['FIFO','PRIORITY','LIFO'][i],9.30+i*1.0,4.6,.95,.22,8,'DCE8EE',True,align=PP_ALIGN.CENTER)
txt(s,'PEARSON HND COMPUTING  /  UNIT 19',.72,.72,7,.28,10,'76D6C4',True)
txt(s,'Data Structures\n& Algorithms',.72,1.48,8.1,1.85,33,WHITE,True)
txt(s,'SOC Alert Management Backend',.76,3.56,7,.45,18,'DCE8EE')
rect(s,.76,4.42,1.0,.065,fill=TEAL,line=TEAL,radius=False)
txt(s,'WRITTEN TECHNICAL PRESENTATION',.76,4.76,5.4,.25,9,'76D6C4',True)
for i,t in enumerate(['Student: [INSERT NAME]','ID: [INSERT ID]','Tutor: [INSERT TUTOR]','Assignment: [INSERT TITLE]']): txt(s,t,.76,5.35+i*.30,5,.22,10,'E5EDF1')
txt(s,'NOVEMBER 2026',9.65,6.74,2.8,.25,9,'DCE8EE',True)
notes(s,'Introduce the SOC assignment and explain that the presentation summarises the tested backend, evidence and limitations. Replace the four clearly marked student/tutor fields before submission.')

# Slide 2 - brief problem
s=base('One SOC intake, two competing service rules','Problem framing',2,'Routine events need a fair arrival order; critical incidents need a faster response path.')
kpi(s,.65,2.05,3.75,'Routine path','FIFO',TEAL,'Oldest queued event first')
kpi(s,4.78,2.05,3.75,'Urgent path','Priority',AMBER,'Severity → timestamp → stable tie')
kpi(s,8.90,2.05,3.75,'Analyst support','Live events',GREEN,'Lifecycle updates and action history')
rect(s,.65,3.8,12,2.25,fill=WHITE,line=LIGHT)
txt(s,'DESIGN REQUIREMENTS',.92,4.08,3,.26,10,TEAL,True)
items=['Maintain alert ID, status and timestamps','Process routine alerts sequentially','Select HIGH / CRITICAL alerts before routine work','Publish analyst-visible changes safely','Handle empty, invalid, duplicate and capacity cases']
for i,it in enumerate(items):
    yy=4.48+i*.30; rect(s,1.02,yy+.035,.12,.12,fill=TEAL,line=TEAL,radius=True); txt(s,it,1.28,yy,10.5,.23,11,INK)
notes(s,'Frame the scenario as two queueing policies rather than one global FIFO. Emphasise the separate needs of traceability and urgency. These are derived from the supplied assignment brief.')

# Slide 3 - data flow
s=base('Separate scheduling, shared record of truth','System design',3,'One validated alert record feeds the correct scheduling structure and the same update channel.')
add_image(s,'figure-01-soc-data-flow.png',.6,1.8,12.0,4.95)
notes(s,'Walk left to right through event ingestion, validation and registry insertion. Explain the severity router, routine FIFO and priority heap. Both paths converge on the processor, while the registry provides current alert snapshots and subscribers receive state events.')

# Slide 4 - ADT roles
s=base('Each structure is selected for its access pattern','Selected structures',4,'The system combines complementary contracts; no single structure is optimal for every operation.')
for x,title,accent,items in [(.7,'LINKED FIFO',TEAL,['enqueue at tail','dequeue at head','O(1) / O(1)','routine fairness']), (4.55,'BINARY MAX-HEAP',AMBER,['highest severity first','earliest timestamp next','stable sequence tie-break','add / pop O(log n)']), (8.4,'ARRAY STACK','8064A2',['push / pop / peek','last-in, first-out','O(1) top operations','bounded analyst undo'])]:
    rect(s,x,2.0,3.55,3.55,fill=WHITE,line=LIGHT)
    rect(s,x,2.0,3.55,.12,fill=accent,line=accent,radius=False)
    txt(s,title,x+.2,2.36,3.12,.32,12,accent,True)
    for j,item in enumerate(items): txt(s,'• '+item,x+.24,3.0+j*.48,3.0,.28,10.5,INK)
rect(s,.7,5.95,11.25,.62,fill='EAF3F5',line='EAF3F5')
txt(s,'FIFO: A → B → C     |     LIFO: push A, B, C → pop C, B, A',.95,6.13,10.7,.23,11,NAVY,True,align=PP_ALIGN.CENTER)
notes(s,'Explain queue/heap/stack semantics and why each is used. FIFO means earliest in first out; LIFO means newest item first. Routine alerts use the linked queue, high/critical alerts use the heap, and analyst action history uses the stack.')

# Slide 5 - class diagram
s=base('Encapsulation protects alert invariants','Object model',5,'Private state, public operations and immutable snapshots keep clients away from representation details.')
add_image(s,'figure-02-uml-class-diagram.png',.75,1.75,11.8,4.95)
notes(s,'Explain Alert and AlertEvent as immutable values. AlertManager composes the custom structures, index map, subscribers and lock. Public methods enforce valid operations; private members hide nodes and heap internals. ADTs are a strong foundation for OO but do not alone define inheritance or dynamic dispatch.')

# Slide 6 - formal contracts
s=base('ADT contracts make valid operations explicit','Formal specification',6,'Preconditions guard invalid states; postconditions define what a client can rely on.')
rows=[('Queue.Enqueue(a)','size(Q) < capacity','Q′ = Q ⧺ [a]'),('Queue.Dequeue()','size(Q) > 0','returns head(Q); Q′ = tail(Q)'),('Priority.Pop()','size(P) > 0','returns arg max rank(P)'),('Stack.Pop()','size(S) > 0','returns last(S); removes last'),('Manager.Add(id,sev,t)','ID new; severity valid; capacity available','record stored and routed once')]
# lightweight contract table
x0=.72; y0=2.0; widths=[3.15,3.5,4.55]; hh=.62
for j,label in enumerate(['OPERATION','PRECONDITION','POSTCONDITION']):
    x=x0+sum(widths[:j]); rect(s,x,y0,widths[j],hh,fill=NAVY,line=NAVY,radius=False); txt(s,label,x+.12,y0+.19,widths[j]-.2,.22,8,WHITE,True)
for i,row in enumerate(rows):
    yy=y0+hh+i*.67
    for j,val in enumerate(row):
        x=x0+sum(widths[:j]); rect(s,x,yy,widths[j],.64,fill=WHITE if i%2==0 else PALE,line=LIGHT,radius=False); txt(s,val,x+.12,yy+.13,widths[j]-.22,.38,10,INK,j==0)
notes(s,'This is a compact view of the formal imperative specification. Queue operations preserve FIFO, stack operations preserve LIFO, and priority pop returns the maximum rank. Rank is severity descending, receive time ascending and insertion sequence ascending.')

# Slide 7 - implementation
s=base('Priority ordering is encoded as a total key','Implementation highlight',7,'The sequence counter preserves arrival stability when severity and timestamps tie.')
rich_code(s,'def _priority_key(alert, sequence):\n    return (int(alert.severity),\n            -alert.received_at.timestamp(), -sequence)\n\ndef pop(self):\n    if not self._heap:\n        raise QueueEmptyError("cannot pop from an empty queue")\n    root = self._heap[0].alert\n    last = self._heap.pop()\n    if self._heap:\n        self._heap[0] = last\n        self._sift_down(0)\n    return root',.7,2.0,7.0,4.65)
rect(s,8.05,2.0,4.2,4.65,fill=WHITE,line=LIGHT)
txt(s,'SELECTION RULE',8.35,2.35,3.4,.28,10,TEAL,True)
for i,(big,small,co) in enumerate([('1','Severity descending',AMBER),('2','Received time ascending',TEAL),('3','Insertion sequence ascending',GREEN)]):
    yy=3.0+i*1.0; pill(s,big,8.35,yy,.48,co); txt(s,small,9.02,yy+.04,2.85,.35,11,INK,True)
txt(s,'Heap root is selected first. Sift-up and sift-down repair the heap in O(log n).',8.35,6.05,3.35,.42,9,SLATE)
notes(s,'Explain how the tuple order implements the business policy. A max-heap places the largest key at the root. Negated timestamp and sequence components make earlier values compare as larger. Empty removal raises a named error instead of returning a sentinel.')

# Slide 8 tests
s=base('Tests cover the invariants that matter operationally','Testing & errors',8,'Test-first development: the original suite failed before implementation, then grew to 24 passing tests.')
kpi(s,.72,2.05,2.75,'Final suite','24 / 24',GREEN,'pytest tests passed')
kpi(s,3.75,2.05,2.75,'Concurrency','50 alerts',TEAL,'8 worker threads')
kpi(s,6.78,2.05,2.75,'Capacity','bounded',AMBER,'queue / stack limits')
kpi(s,9.80,2.05,2.75,'Observers','isolated',GREEN,'listener fault handling')
rect(s,.72,3.8,11.83,2.3,fill=WHITE,line=LIGHT)
for i,t in enumerate(['Empty queue and stack operations','Duplicate ID and unknown severity','Priority timestamp tie-breaking and stable ties','Illegal alert state transitions and missing IDs','Dismissed pending item and observer exceptions','Concurrent ingestion and shortest-path edge cases']):
    xx=.98+(i//3)*5.65; yy=4.08+(i%3)*.56
    pill(s,'PASS',xx,yy,.66,GREEN); txt(s,t,xx+.82,yy+.04,4.6,.26,9.5,INK)
notes(s,'The first red run is preserved in results/tdd-red.txt. The current test suite contains 24 tests. Discuss important failure paths and explain that in-memory listener notification is a demonstration rather than durable message delivery.')

# Slide 9 Big-O
s=base('Complexity supports the structure choices','Big-O summary',9,'Asymptotic bounds describe growth; they do not predict every constant factor in CPython.')
rows=[('Linked queue','enqueue / dequeue','O(1)','O(n) stored'),('Array stack','push / pop / peek','O(1)','O(C) allocated'),('Binary heap','add / pop / peek','O(log n) / O(1)','O(n)'),('ID dictionary','lookup (average)','O(1)','O(n)'),('Insertion sort','worst-case','O(n²)','O(1) extra'),('Merge sort','all cases','O(n log n)','O(n) extra'),('Dijkstra','lazy heap','O((V+E) log V)','O(V+E)'),('Bellman–Ford','edge relaxation','O(VE)','O(V+E)')]
ws=[2.4,2.8,2.7,2.3]; x0=.72; y0=1.95; rh=.52
for j,hdr in enumerate(['STRUCTURE','OPERATION','TIME','SPACE']):
    xx=x0+sum(ws[:j]); rect(s,xx,y0,ws[j],.48,fill=NAVY,line=NAVY,radius=False); txt(s,hdr,xx+.1,y0+.14,ws[j]-.2,.2,8,WHITE,True)
for i,row in enumerate(rows):
    yy=y0+.48+i*rh
    for j,val in enumerate(row):
        xx=x0+sum(ws[:j]); rect(s,xx,yy,ws[j],rh,fill=WHITE if i%2==0 else PALE,line=LIGHT,radius=False); txt(s,val,xx+.1,yy+.13,ws[j]-.2,.24,9.3,INK,j==0)
notes(s,'Explain that n denotes stored items, C is stack capacity, V vertices, E edges. Dijkstra uses a lazy binary heap with nonnegative weights. Bellman–Ford supports negative edges and detects reachable negative cycles.')

# Slide 10 queue benchmark
s=base('FIFO: the list becomes expensive at scale','Measured evaluation',10,'Median milliseconds; complete build-and-drain cycle; five runs per size on the project VPS.')
add_image(s,'figure-03-fifo-scaling.png',.75,1.75,8.05,4.75)
rect(s,9.1,2.0,3.3,3.95,fill=WHITE,line=LIGHT)
txt(s,'AT n = 16,000',9.4,2.37,2.7,.25,9,TEAL,True)
txt(s,'6.04 ms',9.4,2.85,2.4,.52,25,NAVY,True)
txt(s,'custom linked FIFO',9.4,3.42,2.5,.25,9,SLATE)
txt(s,'15.28 ms',9.4,4.12,2.5,.50,22,AMBER,True)
txt(s,'list pop(0)',9.4,4.66,2.5,.25,9,SLATE)
txt(s,'Linked queue uses more memory; list is faster at small n.',9.4,5.30,2.55,.45,9,INK)
notes(s,'At 250 entries the list is quicker, but at 16,000 the linked queue is 6.04ms while list pop(0) is 15.28ms. The crossover is caused by repeated shifting in the list. Do not claim linked lists are always faster; memory overhead is almost double at 5,000 items.')

# Slide 11 priority benchmark
s=base('Priority heap: better asymptotic growth, slower here','Measured evaluation',11,'Custom Python sift operations have higher constants than optimized bisect and list operations.')
add_image(s,'figure-04-priority-scaling.png',.72,1.78,8.05,4.72)
rect(s,9.1,2.0,3.3,3.95,fill=WHITE,line=LIGHT)
txt(s,'AT n = 16,000',9.4,2.37,2.7,.25,9,AMBER,True)
txt(s,'91.67 ms',9.4,2.88,2.4,.50,24,NAVY,True)
txt(s,'custom binary heap',9.4,3.42,2.7,.25,9,SLATE)
txt(s,'52.17 ms',9.4,4.12,2.5,.50,22,TEAL,True)
txt(s,'dynamic sorted list',9.4,4.66,2.5,.25,9,SLATE)
txt(s,'Measured constants do not overturn O(n log n) vs O(n²).',9.4,5.30,2.55,.48,9,INK)
notes(s,'The benchmark compares the custom heap to a dynamically sorted list using bisect insertion. The sorted list is faster across this measured range because key search and reference shifts are implemented in optimized runtime code, while the heap operations run in Python. The heap remains the more scalable ADT based on asymptotic insertion/removal guarantees; validate production workload and possibly use native priority structures.')

# Slide 12 sort and graph
s=base('Algorithm choice depends on data shape and constraints','Algorithm comparison',12,'The assignment also evaluates sorting and shortest paths beyond the alert scheduler.')
add_image(s,'figure-05-sorting-scaling.png',.68,1.72,6.55,4.25)
add_image(s,'figure-07-shortest-path-example.png',7.48,1.78,5.2,3.1)
rect(s,7.65,5.12,4.65,.85,fill='EAF3F5',line='EAF3F5')
txt(s,'Dijkstra = 8   |   Bellman–Ford = 8',7.9,5.38,4.1,.28,12,TEAL,True,align=PP_ALIGN.CENTER)
txt(s,'Dijkstra requires non-negative weights. Bellman–Ford supports negative edges and flags negative cycles.',7.65,6.15,4.7,.42,9,SLATE)
notes(s,'Insertion sort is stable and in-place but O(n^2) average/worst-case; merge sort is stable O(n log n) using O(n) extra memory. Dijkstra is the efficient route choice for nonnegative costs; Bellman–Ford is more general but O(VE). Example path cost is 8.')

# Slide 13 memory
s=base('The linked queue trades memory for cheaper front removal','Storage evaluation',13,'Peak traced Python allocations when constructing 5,000 items.')
add_image(s,'figure-06-memory-profile.png',.78,1.85,7.1,4.45)
rect(s,8.35,2.15,3.75,3.8,fill=WHITE,line=LIGHT)
txt(s,'187.5 KiB',8.7,2.55,3.0,.52,23,SLATE,True)
txt(s,'Python list',8.7,3.08,2.7,.25,10,SLATE)
txt(s,'382.8 KiB',8.7,3.85,3.0,.52,23,TEAL,True)
txt(s,'Custom linked queue',8.7,4.38,2.8,.25,10,SLATE)
txt(s,'tracemalloc peak; not total process RSS',8.7,5.25,2.9,.35,8,SLATE)
notes(s,'Explain that Python list peak is 191,952 bytes and linked queue is 391,992 bytes, measured with tracemalloc. The linked node representation incurs extra Python objects and references. This is a relevant tradeoff for a memory-constrained SOC service.')

# Slide 14 recommendations
s=base('Keep the contracts; harden the deployment','Conclusion & recommendations',14,'The data-structure choices are justified for the assignment; operational readiness needs additional controls.')
for x,title,accent,lines in [(.7,'DELIVERED',TEAL,['24 passing tests','FIFO + priority + LIFO','Seven diagram/chart assets','Measured timing and memory']), (4.55,'LIMITATIONS',AMBER,['In-memory, one process','No durable persistence','Synchronous callbacks','Strict priority can starve routine work']), (8.4,'NEXT STEPS',GREEN,['Transactional repository + event log','Async message bus and retries','Auth, audit and observability','Ageing / fair scheduling policy'])]:
    rect(s,x,2.0,3.55,3.75,fill=WHITE,line=LIGHT)
    rect(s,x,2.0,3.55,.12,fill=accent,line=accent,radius=False)
    txt(s,title,x+.2,2.37,3.05,.28,11,accent,True)
    for i,line in enumerate(lines):
        txt(s,'• '+line,x+.22,3.0+i*.55,3.05,.38,10,INK)
rect(s,.7,6.05,11.25,.56,fill=NAVY,line=NAVY)
txt(s,'CORE DECISION: use a linked FIFO for routine work and a heap for urgency; measure before production tuning.',.95,6.20,10.7,.24,10,WHITE,True,align=PP_ALIGN.CENTER)
notes(s,'Conclude by distinguishing assignment completeness from operational production readiness. Recommend durable records, asynchronous delivery, authentication, telemetry, and a starvation policy. Remind the presenter to replace placeholders.')

out=ROOT/'slides'/'Unit19_DSA_SOC_Alerts_Presentation.pptx'
prs.core_properties.title='Unit 19 DSA — SOC Alert Management'
prs.core_properties.subject='Data structures, algorithms, implementation and empirical evaluation'
prs.core_properties.author='[STUDENT NAME]'
prs.core_properties.keywords='Pearson HND, Unit 19, SOC, FIFO, heap, stack, Big-O'
prs.save(out)
print(json.dumps({'pptx':str(out),'slides':len(prs.slides),'speaker_notes':sum(bool(slide.has_notes_slide) for slide in prs.slides)},indent=2))
