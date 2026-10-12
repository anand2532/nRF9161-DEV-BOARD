import pcbnew,sys,json
from collections import defaultdict
P=sys.argv[1]; mode=sys.argv[2]; b=pcbnew.LoadBoard(P)
HOLD={"ANT","ANT_FIT","AUX","AUX_FIT","GPS","GNSS_ANT","GNSS_VBIAS","GNSS_VBIAS_SRC"}
tr=[t for t in b.GetTracks() if t.Type()!=pcbnew.PCB_VIA_T and str(t.GetNetname()) not in HOLD]
rm=set(); out=[]
def on(p,t):
    s,e=t.GetStart(),t.GetEnd(); L2=((e.x-s.x)**2+(e.y-s.y)**2)
    if L2==0: return p==s
    cr=(e.x-s.x)*(p.y-s.y)-(e.y-s.y)*(p.x-s.x)
    if abs(cr)/L2**0.5>1000: return False
    d=((p.x-s.x)*(e.x-s.x)+(p.y-s.y)*(e.y-s.y))/L2
    return -1e-6<=d<=1+1e-6
g=defaultdict(list)
for t in tr: g[(str(t.GetNetname()),t.GetLayer())].append(t)
for k,L in g.items():
    L=sorted(L,key=lambda t:(-t.GetLength(),-t.GetWidth()))
    for i,c in enumerate(L):
        if id(c) in rm: continue
        for a in L[:i]:
            if id(a) in rm or a.GetWidth()<c.GetWidth(): continue
            same=sorted([(a.GetStart().x,a.GetStart().y),(a.GetEnd().x,a.GetEnd().y)])==sorted([(c.GetStart().x,c.GetStart().y),(c.GetEnd().x,c.GetEnd().y)])
            if same or (mode=="contained" and on(c.GetStart(),a) and on(c.GetEnd(),a)):
                rm.add(id(c)); out.append((k[0],b.GetLayerName(k[1]),"exact" if same else "contained",round(c.GetLength()/1e6,3))); break
for t in tr:
    if id(t) in rm: b.Remove(t)
b.Save(P); json.dump(out,open("/tmp/cc/dedup_%s.json"%mode,"w"),indent=0)
from collections import Counter; print(len(out),Counter(x[2] for x in out))
