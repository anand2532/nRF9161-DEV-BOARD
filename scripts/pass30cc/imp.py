import pcbnew,re,sys,json
ses,out=sys.argv[1],sys.argv[2]; skip=set(sys.argv[3].split(",")) if len(sys.argv)>3 and sys.argv[3] else set()
B="/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
b=pcbnew.LoadBoard(B); RIP=set(sys.argv[4].split(",")) if len(sys.argv)>4 and sys.argv[4] else set()
for t in list(b.GetTracks()):
    if str(t.GetNetname()) in RIP: b.Remove(t)
import os
ONLY=set(open("/tmp/cc/open_nets.txt").read().split(",")) if os.environ.get("ONLY") else None
if ONLY: ONLY={x.strip() for x in ONLY}
L={"F.Cu":pcbnew.F_Cu,"In1.Cu":pcbnew.In1_Cu,"In2.Cu":pcbnew.In2_Cu,"B.Cu":pcbnew.B_Cu}
txt=open(ses).read(); tok=re.findall(r'\(|\)|"[^"]*"|[^\s()]+',txt)
def parse(i):
    l=[];i+=1
    while tok[i]!=")":
        if tok[i]=="(": x,i=parse(i); l.append(x)
        else: l.append(tok[i].strip('"')); i+=1
    return l,i+1
tree,_=parse(0)
def find(t,k):
    for x in t:
        if isinstance(x,list):
            if x and x[0]==k: yield x
            yield from find(x,k)
net_out=next(find(tree,"network_out"))
P=lambda x,y:pcbnew.VECTOR2I(int(round(float(x)*100)),int(round(-float(y)*100)))
stats={}
for n in net_out[1:]:
    if not isinstance(n,list) or n[0]!="net": continue
    name=n[1]
    if name in skip: continue
    if ONLY and name not in ONLY: continue
    net=b.FindNet(name); s=stats.setdefault(name,{"seg":0,"via":0,"len":0.0})
    for it in n[2:]:
        if it[0]=="wire":
            p=it[1]; lay=L[p[1]]; w=int(float(p[2])*100); pts=p[3:]
            pts=[q for q in pts if not isinstance(q,list)]
            for k in range(0,len(pts)-2,2):
                a,c=P(pts[k],pts[k+1]),P(pts[k+2],pts[k+3])
                if a==c: continue
                t=pcbnew.PCB_TRACK(b);t.SetStart(a);t.SetEnd(c);t.SetWidth(w);t.SetLayer(lay);t.SetNet(net);b.Add(t)
                s["seg"]+=1; s["len"]+=t.GetLength()/1e6
        elif it[0]=="via":
            v=pcbnew.PCB_VIA(b); v.SetPosition(P(it[2],it[3])); v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
            v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNet(net); b.Add(v); s["via"]+=1
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(B)
json.dump(stats,open(out,"w"),indent=1); print(json.dumps(stats))
