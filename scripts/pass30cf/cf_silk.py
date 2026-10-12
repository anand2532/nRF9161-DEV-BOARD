import pcbnew,sys,json,math,re
o=pcbnew.LoadBoard("/tmp/cc/orig_labels.kicad_pcb")
rowuu=set()
for t in o.GetDrawings():
    if t.GetClass()=="PCB_TEXT":
        y=t.GetPosition().y/1e6
        if abs(y-74)<0.3 or abs(y-60.2)<0.3: rowuu.add(t.m_Uuid.AsString())
P=sys.argv[1]; b=pcbnew.LoadBoard(P); FP={f.GetReference():f for f in b.GetFootprints()}; mm=pcbnew.FromMM; V=lambda x,y:pcbnew.VECTOR2I(mm(x),mm(y))
log={"removed_text":[],"labels":[],"trimmed":[],"moved":[],"hidden":[]}
DROP={"56cbdfb9-4d42-4a0d-b513-de2dc7cdc5d5":"stray '1'","8d1697a3-fb61-43f2-be8f-43b7847ace33":"duplicate title nRF9161-DEV-BOARD (36,3.0)","240d329b-d3fd-4e4b-831d-5ebce8b4bff8":"duplicate subtitle 'nRF9161 DEVELOPMENT BOARD'","57d6270f-b5b4-44da-9872-fed4cbf436c3":"duplicate 'LTE/NR+' (0.8 mm)","ba79314d-ed8e-40b0-92db-ca812c46580b":"duplicate 'GNSS' (0.8 mm)"}
fixedtexts=[]
def newtext(s,x,y,h,th,ang,just=None):
    t=pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetTextSize(pcbnew.VECTOR2I(mm(h),mm(h))); t.SetTextThickness(mm(th)); t.SetTextAngleDegrees(ang)
    if just: t.SetHorizJustify(just)
    t.SetPosition(V(x,y)); b.Add(t); return t
for ref,ytop in (("J12",74.56),("J13",74.56),("J18",60.56)):
    f=FP[ref]
    for p in f.Pads():
        n=str(p.GetNetname()); s={"VDD_GPIO":"3V3"}.get(n,n) if n else "NC"
        x=p.GetPosition().x/1e6
        t=newtext(s,x,ytop-0.3,0.7,0.12,90,pcbnew.GR_TEXT_H_ALIGN_LEFT); fixedtexts.append(t); log["labels"].append((ref,p.GetNumber(),s,x))
    p1=[p for p in f.Pads() if p.GetNumber()=="1"][0]; c=p1.GetPosition()
    d=pcbnew.PCB_SHAPE(b); d.SetShape(pcbnew.SHAPE_T_CIRCLE); d.SetLayer(pcbnew.F_SilkS); d.SetFilled(True); d.SetCenter(pcbnew.VECTOR2I(c.x-mm(1.95),c.y-mm(1.35))); d.SetEnd(pcbnew.VECTOR2I(c.x-mm(1.95)+mm(0.3),c.y-mm(1.35))); d.SetWidth(mm(0.1)); b.Add(d)
j16=FP["J16"]; dnf=newtext("DNF",111.2,8.0,1.0,0.15,90)
# trim U1/U4 silk off pads
def padboxes(f):
    out=[]
    for p in f.Pads():
        bb=p.GetBoundingBox(); bb.Inflate(mm(0.05)+max(0,p.GetSolderMaskExpansion(pcbnew.F_Mask)) + mm(0.15)); out.append(bb)
    return out
for ref in ("U1","U4"):
    f=FP[ref]; pb=padboxes(f)
    for g in list(f.GraphicalItems()):
        if g.GetLayer()!=pcbnew.F_SilkS or g.GetClass()!="PCB_SHAPE": continue
        if g.GetShape()==pcbnew.SHAPE_T_RECT:
            s,e=g.GetStart(),g.GetEnd(); pts=[(s.x,s.y),(e.x,s.y),(e.x,e.y),(s.x,e.y)]
            segs=[(pts[i],pts[(i+1)%4]) for i in range(4)]; w=g.GetWidth()
        elif g.GetShape()==pcbnew.SHAPE_T_SEGMENT:
            segs=[((g.GetStart().x,g.GetStart().y),(g.GetEnd().x,g.GetEnd().y))]; w=g.GetWidth()
        else: continue
        hit=False; keep=[]
        for (a,c) in segs:
            N=max(2,int(math.hypot(c[0]-a[0],c[1]-a[1])/mm(0.02)))
            run=[]; 
            for k in range(N+1):
                x=a[0]+(c[0]-a[0])*k/N; y=a[1]+(c[1]-a[1])*k/N
                bad=any(bb.Inflate(0) is None or (bb.GetLeft()-w/2<=x<=bb.GetRight()+w/2 and bb.GetTop()-w/2<=y<=bb.GetBottom()+w/2) for bb in pb)
                if bad: hit=True
                if not bad: run.append((x,y))
                elif run: keep.append((run[0],run[-1])); run=[]
            if run: keep.append((run[0],run[-1]))
        if not hit: continue
        f.Remove(g); log["trimmed"].append((ref,len(segs),len(keep)))
        for a,c in keep:
            if math.hypot(c[0]-a[0],c[1]-a[1])<mm(0.2): continue
            n=pcbnew.PCB_SHAPE(f); n.SetShape(pcbnew.SHAPE_T_SEGMENT); n.SetLayer(pcbnew.F_SilkS); n.SetWidth(w)
            n.SetStart(pcbnew.VECTOR2I(int(a[0]),int(a[1]))); n.SetEnd(pcbnew.VECTOR2I(int(c[0]),int(c[1]))); f.Add(n)
for t in list(b.GetDrawings()):
    if t.GetClass()!="PCB_TEXT": continue
    u=t.m_Uuid.AsString()
    if u in DROP: log["removed_text"].append(DROP[u]); b.Remove(t)
    elif u in rowuu: b.Remove(t)
b.Save(P); json.dump(log,open("/tmp/cc/cf_silk_log.json","w"),indent=0)
print(log["removed_text"],len(log["labels"]),log["trimmed"])
