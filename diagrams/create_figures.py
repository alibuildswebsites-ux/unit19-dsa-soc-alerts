"""Render source-backed report figures from measured benchmark JSON."""
from __future__ import annotations
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'diagrams'
RESULTS = json.loads((ROOT / 'results/benchmark-results.json').read_text())
# Restrained academic palette: ink, teal, slate, amber.
INK = '#18324A'; TEAL = '#087F8C'; SLATE = '#627588'; AMBER = '#C58B3D'; PALE = '#F3F7F9'; LIGHT = '#E2EBEF'; WHITE = '#FFFFFF'; GREEN = '#3A806C'; RED = '#B85C52'
plt.rcParams.update({'font.family':'Lato','font.size':10,'axes.titlesize':16,'axes.labelsize':11,'axes.titleweight':'bold','text.color':INK,'axes.labelcolor':INK,'xtick.color':SLATE,'ytick.color':SLATE,'axes.edgecolor':LIGHT,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':WHITE,'axes.facecolor':WHITE,'savefig.facecolor':WHITE})

def save(fig, name):
    fig.savefig(OUT/f'{name}.png', dpi=220, bbox_inches='tight', facecolor=WHITE)
    fig.savefig(OUT/f'{name}.svg', bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)

def box(ax, xy, wh, title, lines, fill=PALE, edge=TEAL, title_color=INK):
    x,y=xy; w,h=wh
    p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.08',linewidth=1.3,edgecolor=edge,facecolor=fill)
    ax.add_patch(p)
    ax.text(x+w/2,y+h-0.26,title,ha='center',va='center',fontsize=10.5,fontweight='bold',color=title_color)
    if lines:
        ax.text(x+0.12,y+h-0.53,'\n'.join(lines),ha='left',va='top',fontsize=8.1,color=INK,linespacing=1.4)
    return p

def arrow(ax, start, end, label=None, color=SLATE, rad=0.0):
    a=FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=13,linewidth=1.5,color=color,connectionstyle=f'arc3,rad={rad}')
    ax.add_patch(a)
    if label:
        mx=(start[0]+end[0])/2; my=(start[1]+end[1])/2
        ax.text(mx,my+0.08,label,ha='center',va='bottom',fontsize=8,color=color,bbox=dict(boxstyle='round,pad=0.15',facecolor=WHITE,edgecolor='none',alpha=.95))

def fig_flow():
    fig,ax=plt.subplots(figsize=(13,7.2)); ax.set_xlim(0,13); ax.set_ylim(0,7.2); ax.axis('off')
    ax.text(.25,6.85,'SOC ALERT PIPELINE',fontsize=17,fontweight='bold',color=INK)
    ax.text(.25,6.52,'One ingestion path, two scheduling policies, one analyst-facing event stream',fontsize=10,color=SLATE)
    box(ax,(.3,4.65),(1.8,1.15),'Event sources',['Network • identity','EDR • applications'],fill='#F7FAFC',edge=SLATE)
    box(ax,(2.65,4.65),(1.8,1.15),'Ingress validation',['ID • severity','UTC timestamp'],fill='#F7FAFC',edge=SLATE)
    box(ax,(5.05,4.65),(2.0,1.15),'Alert registry',['ID → immutable snapshot','O(1) avg lookup'],fill='#EFF7F7',edge=TEAL)
    box(ax,(7.85,4.65),(1.9,1.15),'Severity router',['HIGH / CRITICAL?','Yes → priority path'],fill='#FFF8EE',edge=AMBER)
    box(ax,(10.55,5.35),(2.1,1.05),'Binary max-heap',['High severity first','Earlier time • stable tie'],fill='#FFF8EE',edge=AMBER)
    box(ax,(10.55,3.85),(2.1,1.05),'Linked FIFO queue',['Routine alerts','First received • first out'],fill='#EFF7F7',edge=TEAL)
    box(ax,(7.75,2.05),(2.25,1.2),'Alert processor',['Set IN_PROGRESS','Persist new snapshot'],fill='#F1F5F8',edge=SLATE)
    box(ax,(10.55,1.95),(2.1,1.25),'Analyst subscribers',['Alert lifecycle events','Callback errors isolated'],fill='#F0F7F2',edge=GREEN)
    box(ax,(4.8,1.95),(2.25,1.25),'Analyst action stack',['Bounded LIFO history','Undo latest action'],fill='#F6F3FA',edge='#8064A2')
    arrow(ax,(2.1,5.22),(2.65,5.22)); arrow(ax,(4.45,5.22),(5.05,5.22)); arrow(ax,(7.05,5.22),(7.85,5.22))
    arrow(ax,(9.75,5.35),(10.55,5.82),'yes',AMBER); arrow(ax,(9.75,4.95),(10.55,4.36),'no',TEAL)
    arrow(ax,(11.6,5.35),(9.6,3.25),None,AMBER,rad=.10); arrow(ax,(11.6,3.85),(9.55,3.25),None,TEAL,rad=-.08)
    arrow(ax,(10.0,2.65),(10.55,2.65),'publish',GREEN)
    arrow(ax,(5.95,3.15),(7.75,2.8),'analyst action', '#8064A2')
    arrow(ax,(6.0,4.65),(6.0,3.2),'retrieve by ID',SLATE)
    ax.text(.35,.75,'Consistency note: the registry is the source of truth; queue/heap entries select work, while immutable snapshots and lifecycle rules protect state.',fontsize=9.2,color=SLATE)
    save(fig,'figure-01-soc-data-flow')

def fig_uml():
    fig,ax=plt.subplots(figsize=(14,9)); ax.set_xlim(0,14); ax.set_ylim(0,9); ax.axis('off')
    ax.text(.3,8.62,'UML CLASS VIEW',fontsize=17,fontweight='bold',color=INK)
    ax.text(.3,8.30,'Domain objects, encapsulated structures and coordination responsibilities',fontsize=10,color=SLATE)
    def cls(x,y,w,h,name,attrs,ops,edge=TEAL):
        p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.04',linewidth=1.4,edgecolor=edge,facecolor=WHITE)
        ax.add_patch(p); ax.add_patch(FancyBboxPatch((x,y+h-.38),w,.38,boxstyle='round,pad=0.02,rounding_size=0.04',linewidth=0,facecolor=edge))
        ax.text(x+w/2,y+h-.19,name,ha='center',va='center',color=WHITE,fontweight='bold',fontsize=10)
        yy=y+h-.55
        for line in attrs:
            ax.text(x+.12,yy,line,fontsize=7.4,color=INK,va='top'); yy-=.19
        yy-=.08
        for line in ops:
            ax.text(x+.12,yy,line,fontsize=7.3,color=SLATE,va='top'); yy-=.19
        return (x,y,w,h)
    a=cls(.4,5.45,3.0,2.25,'Alert',['- identifier: str','- severity: Severity','- received_at: datetime','- status: AlertStatus','- updated_at: datetime'],['+ immutable snapshot'],edge=SLATE)
    e=cls(4.15,5.6,2.65,1.9,'AlertEvent',['- event_type: str','- alert: Alert','- emitted_at: datetime'],['+ frozen event'],edge=GREEN)
    m=cls(8.0,4.35,5.3,3.35,'AlertManager',['- _by_id: dict[str, Alert]','- _routine: LinkedQueue[Alert]','- _priority: PriorityAlertQueue','- _analyst_actions: ArrayStack[str]','- _listeners: list[AlertListener]','- _lock: RLock'],['+ add_alert(...)','+ process_next()','+ update_status(...)','+ get_alert(id)','+ subscribe(listener)'],edge=INK)
    q=cls(.4,1.65,3.0,2.65,'LinkedQueue[T]',['- _head: Node[T]','- _tail: Node[T]','- _size: int'],['+ enqueue(value)','+ dequeue()','+ peek()','+ is_empty()'],edge=TEAL)
    h=cls(4.0,1.65,3.0,2.65,'PriorityAlertQueue',['- _heap: list[Entry]','- _sequence: int'],['+ add(alert)','+ pop()','+ peek()','- _sift_up(i)','- _sift_down(i)'],edge=AMBER)
    s=cls(7.65,1.65,2.8,2.65,'ArrayStack[T]',['- _items: list[T]','- _top: int','- _capacity: int'],['+ push(value)','+ pop()','+ peek()'],edge='#8064A2')
    d=cls(11.0,1.65,2.55,2.65,'Severity / Status',['+ INFO…CRITICAL','+ QUEUED','+ IN_PROGRESS','+ RESOLVED','+ DISMISSED'],['enumerations'],edge=SLATE)
    # Relationships are association/composition at the educational design level.
    arrow(ax,(3.4,6.45),(4.15,6.45),'payload',SLATE)
    arrow(ax,(6.8,6.45),(8.0,6.45),'notifies',GREEN)
    arrow(ax,(9.3,4.35),(2.8,4.30),'uses',TEAL,rad=.12)
    arrow(ax,(10.0,4.35),(5.5,4.30),'uses',AMBER,rad=.10)
    arrow(ax,(10.65,4.35),(9.0,4.30),'uses', '#8064A2',rad=.08)
    arrow(ax,(11.85,4.35),(12.25,4.30),'validates',SLATE)
    ax.text(.55,.8,'Legend: private members (−) are accessed only through public operations (+); Alert snapshots and AlertEvent objects are immutable.',fontsize=9,color=SLATE)
    save(fig,'figure-02-uml-class-diagram')

def line_chart(rows,xfield,series,title,ylabel,name,labels):
    fig,ax=plt.subplots(figsize=(8.7,4.7))
    x=[r[xfield] for r in rows]
    palette=[TEAL,AMBER,SLATE]
    for i,(key,label) in enumerate(zip(series,labels)):
        y=[r[key] for r in rows]
        ax.plot(x,y,marker='o',linewidth=2.3,markersize=6,color=palette[i],label=label)
        for xx,yy in zip(x,y):
            ax.annotate(f'{yy:.2f}',(xx,yy),xytext=(0,8 if i==0 else -15),textcoords='offset points',ha='center',fontsize=7,color=palette[i])
    ax.set_title(title,loc='left',pad=14,color=INK); ax.set_xlabel('Input size (n)'); ax.set_ylabel(ylabel); ax.set_xscale('log',base=2); ax.set_yscale('log',base=10); ax.grid(True,which='both',axis='y',color=LIGHT,linewidth=.8); ax.legend(frameon=False,loc='upper left');
    ax.text(0,-.23,'Measured on one VPS vCPU; median of five runs. These are implementation timings, not universal constants.',transform=ax.transAxes,fontsize=8,color=SLATE)
    save(fig,name)

fig_flow()
fig_uml()

line_chart(RESULTS['fifo_scaling'],'n',['linked_queue_ms','python_list_fifo_ms'],'FIFO end-to-end cycle: linked queue vs list pop(0)','Median time (ms)','figure-03-fifo-scaling',['Custom linked FIFO queue','Python list FIFO (pop(0))'])
line_chart(RESULTS['priority_scaling'],'n',['binary_heap_ms','sorted_list_ms'],'Priority cycle: binary heap vs dynamically sorted list','Median time (ms)','figure-04-priority-scaling',['Custom binary max-heap','Sorted list (bisect insertion)'])
line_chart(RESULTS['sorting_scaling'],'n',['insertion_sort_ms','merge_sort_ms'],'Sorting: insertion sort vs iterative merge sort','Median time (ms)','figure-05-sorting-scaling',['Insertion sort','Merge sort'])

mem=RESULTS['memory_profile']
fig,ax=plt.subplots(figsize=(7.5,4.1)); vals=[mem['python_list_peak_bytes']/1024,mem['linked_queue_peak_bytes']/1024]; bars=ax.bar(['Python list','Custom linked queue'],vals,color=[SLATE,TEAL],width=.56)
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,v+3,f'{v:.1f} KiB',ha='center',fontweight='bold',color=INK)
ax.set_title('Peak traced allocations at n = 5,000',loc='left',pad=14); ax.set_ylabel('KiB'); ax.set_ylim(0,max(vals)*1.25); ax.grid(axis='y',color=LIGHT); ax.set_axisbelow(True)
ax.text(0,-.23,'Python tracemalloc peak; includes the values and container/node allocations, not total process RSS.',transform=ax.transAxes,fontsize=8,color=SLATE)
save(fig,'figure-06-memory-profile')

fig,ax=plt.subplots(figsize=(9,4.8)); ax.set_xlim(-.5,4.7); ax.set_ylim(-.55,2.4); ax.axis('off'); ax.text(-.4,2.15,'WEIGHTED SOC NETWORK',fontsize=16,fontweight='bold',color=INK); ax.text(-.4,1.90,'Example routes from a sensor to an affected server',fontsize=9,color=SLATE)
pts={'Sensor':(.2,.9),'Gateway':(1.9,1.4),'Switch':(2.6,.4),'Server':(4.1,.9)}
for name,(x,y) in pts.items():
 c=Circle((x,y),.24,facecolor=PALE,edgecolor=TEAL,linewidth=1.4); ax.add_patch(c); ax.text(x,y,name,ha='center',va='center',fontsize=8,fontweight='bold',color=INK)
for a,b,w in [('Sensor','Gateway',2),('Sensor','Switch',4),('Gateway','Switch',1),('Gateway','Server',8),('Switch','Server',5)]:
 x1,y1=pts[a]; x2,y2=pts[b]; ax.plot([x1,x2],[y1,y2],color=SLATE,linewidth=1.35,zorder=0); mx=(x1+x2)/2; my=(y1+y2)/2; ax.text(mx,my+.07,str(w),fontsize=8,ha='center',color=AMBER,fontweight='bold',bbox=dict(facecolor=WHITE,edgecolor='none',pad=1))
# highlight shortest path sensor -> gateway -> switch -> server
for a,b in [('Sensor','Gateway'),('Gateway','Switch'),('Switch','Server')]:
 x1,y1=pts[a]; x2,y2=pts[b]; ax.plot([x1,x2],[y1,y2],color=TEAL,linewidth=3,zorder=1,alpha=.8)
ax.text(.1,-.1,'Highlighted shortest path: Sensor → Gateway → Switch → Server = 2 + 1 + 5 = 8',fontsize=9.5,color=TEAL,fontweight='bold')
ax.text(.1,-.37,'Alternative: Sensor → Switch → Server = 4 + 5 = 9; direct via Gateway → Server = 2 + 8 = 10.',fontsize=8.2,color=SLATE)
save(fig,'figure-07-shortest-path-example')

register='''# Figure register and accessible descriptions\n\nAll images were generated from source-backed code or actual benchmark-results.json. Charts in Figures 3–6 use the exact measurements captured by `benchmarks/benchmark.py`; there are no illustrative numbers substituted for measurements.\n\n| Figure | Asset | Description / takeaway |\n|---|---|---|\n| 1 | figure-01-soc-data-flow | Network, identity, EDR and application events enter validation, are recorded by ID, then routed to a severity heap or routine FIFO queue. Both feed the processor and analyst notifications; an array stack supports LIFO analyst-action history. |\n| 2 | figure-02-uml-class-diagram | UML-style class view for Alert, AlertEvent, AlertManager, LinkedQueue, PriorityAlertQueue, ArrayStack and the Severity/Status enums. Private state and public operations indicate encapsulation. |\n| 3 | figure-03-fifo-scaling | Measured time for a complete enqueue/dequeue batch, comparing linked FIFO and list append/pop(0) at n=250, 1,000, 4,000 and 16,000. |\n| 4 | figure-04-priority-scaling | Measured add-all/pop-all cycle for the custom max-heap versus a dynamically sorted list maintained with bisect insertion. |\n| 5 | figure-05-sorting-scaling | Actual timing of stable in-place insertion sort and iterative stable merge sort at n=100, 500 and 1,500. |\n| 6 | figure-06-memory-profile | tracemalloc peak traced allocations for a built Python list and custom linked queue of 5,000 integer values. |\n| 7 | figure-07-shortest-path-example | Weighted network with the highlighted cost-8 shortest route from Sensor to Server; Dijkstra and Bellman–Ford both return 8 on the positive-weight graph. |\n\nFigures are intentionally labelled directly and use shape/annotation in addition to colour. The accompanying report text states what each visual does and does not prove.\n'''
(ROOT/'docs/figure-register.md').write_text(register)
print('generated',len(list(OUT.glob('figure-*.png'))),'PNG figures')
