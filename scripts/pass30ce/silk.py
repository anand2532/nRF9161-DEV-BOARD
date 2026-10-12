import pcbnew,sys,json,math
P=sys.argv[1]; b=pcbnew.LoadBoard(P); mm=pcbnew.FromMM
FS,BS=pcbnew.F_SilkS,pcbnew.B_SilkS
U1=b.FindFootprintByReference("U1").GetBoundingBox(False,False)
EDGE=b.GetBoardEdgesBoundingBox(); EM=mm(0.3); M=mm(0.1)
def box(i,m=0):
    bb=i.GetBoundingBox(); bb.Inflate(m); return bb
fixed={FS:[],BS:[]}
for f in b.GetFootprints():
    for g in f.GraphicalItems():
        if g.GetClass()=="PCB_SHAPE" and g.GetLayer() in fixed: fixed[g.GetLayer()].append(box(g))
    for p in f.Pads():
        for sl,cl in ((FS,pcbnew.F_Mask),(BS,pcbnew.B_Mask)):
            if p.IsOnLayer(cl) or p.IsOnLayer(pcbnew.F_Cu if sl==FS else pcbnew.B_Cu) and p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH:
                bb=p.GetBoundingBox(); bb.Inflate(max(0,p.GetSolderMaskExpansion(cl if hasattr(p,'GetSolderMaskExpansion') else 0)) if False else mm(0.05)); fixed[sl].append(bb)
for d in b.GetDrawings():
    if d.GetClass()=="PCB_SHAPE" and d.GetLayer() in fixed: fixed[d.GetLayer()].append(box(d))
movable=[]
for f in b.GetFootprints():
    r=f.Reference()
    if r.IsVisible() and r.GetLayer() in fixed: movable.append(("ref",r,f))
for d in b.GetDrawings():
    if d.GetClass()=="PCB_TEXT" and d.GetLayer() in fixed: movable.append(("txt",d,None))
def ok(t,others):
    bb=box(t)
    if bb.GetLeft()<EDGE.GetLeft()+EM or bb.GetRight()>EDGE.GetRight()-EM or bb.GetTop()<EDGE.GetTop()+EM or bb.GetBottom()>EDGE.GetBottom()-EM: return False
    bm=box(t,M)
    for o in fixed[t.GetLayer()]:
        if bm.Intersects(o): return False
    for o in others:
        if o is not t and o.GetLayer()==t.GetLayer() and bm.Intersects(box(o)): return False
    return True
texts=[m[1] for m in movable]
log=[];hidden=[]
def state(t): return (t.GetPosition(),t.GetTextAngleDegrees(),t.GetTextHeight(),t.GetTextWidth(),t.GetTextThickness())
def setst(t,s): t.SetPosition(s[0]); t.SetTextAngleDegrees(s[1]); t.SetTextHeight(s[2]); t.SetTextWidth(s[3]); t.SetTextThickness(s[4])
# refs: normalise size
for kind,t,f in movable:
    if kind=="ref":
        t.SetTextHeight(mm(0.8)); t.SetTextWidth(mm(0.8)); t.SetTextThickness(mm(0.15))
        a=t.GetTextAngleDegrees()%180; t.SetTextAngleDegrees(0 if a<45 or a>135 else 90)
        if t.IsKeepUpright and False: pass
# hide refs under U1
for kind,t,f in movable:
    if kind=="ref" and f.GetReference()!="U1" and U1.Contains(f.GetPosition()):
        t.SetVisible(False); hidden.append((f.GetReference(),"under U1"))
active=[t for (k,t,f) in movable if t.IsVisible()]
bad=[t for t in active if not ok(t,active)]
print("initial colliding",len(bad),"of",len(active))
for t in bad:
    kind,_,f=[m for m in movable if m[1] is t][0]
    s0=state(t); o0=t.GetPosition(); placed=False
    if kind=="ref":
        fb=f.GetBoundingBox(False,False); cx,cy=fb.GetCenter().x,fb.GetCenter().y
        sizes=[(0.8,0.15),(0.6,0.12)]
        anchors=[]
        for sz,_ in sizes:
            g=mm(sz/2+0.25)
            anchors.append([(cx,fb.GetTop()-g),(cx,fb.GetBottom()+g),(fb.GetLeft()-g,cy),(fb.GetRight()+g,cy)])
    else:
        sizes=[(s0[2]/1e6,s0[4]/1e6),(0.6,0.12)] if s0[2]>mm(0.6) else [(s0[2]/1e6,s0[4]/1e6)]
        anchors=[[(o0.x,o0.y)] for _ in sizes]
    for (sz,th),anc in zip(sizes,anchors):
        for ang in (0,90) if kind=="ref" else (s0[1]%180,(s0[1]+90)%180):
            for r in [0]+[i*0.2 for i in range(1,26)]:
                steps=max(1,int(2*math.pi*r/0.2)) if r else 1
                for ax,ay in anc:
                    for k in range(steps):
                        th_=2*math.pi*k/steps
                        t.SetTextHeight(mm(sz)); t.SetTextWidth(mm(sz)); t.SetTextThickness(mm(th)); t.SetTextAngleDegrees(ang)
                        t.SetPosition(pcbnew.VECTOR2I(int(ax+mm(r)*math.cos(th_)),int(ay+mm(r)*math.sin(th_))))
                        if ok(t,active): placed=True;break
                    if placed:break
                if placed:break
            if placed:break
        if placed:break
    if placed: log.append((kind,f.GetReference() if f else t.GetText(),round((t.GetPosition()-o0).EuclideanNorm()/1e6,2),t.GetTextHeight()/1e6,t.GetTextAngleDegrees()))
    else:
        setst(t,s0); t.SetVisible(False); active.remove(t); hidden.append((f.GetReference() if f else "text:"+t.GetText()+"@%.2f,%.2f"%(o0.x/1e6,o0.y/1e6),"no space"))
b.Save(P)
json.dump({"moved":log,"hidden":hidden},open("/tmp/cc/silk_log.json","w"),indent=0)
print("moved",len(log),"hidden",len(hidden)); print(hidden)
