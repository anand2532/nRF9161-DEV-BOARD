import pcbnew,sys,json,math
B=sys.argv[1]; b=pcbnew.LoadBoard(B); mm=pcbnew.FromMM
u=b.FindFootprintByReference("U1")
RF={"ANT","ANT_FIT","AUX","AUX_FIT","GPS","GNSS_ANT","GNSS_VBIAS","GNSS_VBIAS_SRC"}
def inkeep(x,y):
    if 0<=x<=24.2 and 20<=y<=64: return "RF"
    if 0<=x<=29 and 26<=y<=40: return "RF2"
    if 27.6<=x<=44.4 and 26.35<=y<=37.86: return "U1"
    if 53<=x<=60 and 12<=y<=22: return "neck"
items=[]
for t in b.GetTracks(): items.append(t)
for p in b.GetPads(): items.append(p)
def check(net,pad,vx,vy,path):
    v=pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(vx),mm(vy))); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetWidth(pcbnew.F_Cu,mm(0.5)) if 0 else None
    k=inkeep(vx,vy)
    if k: return "keepout "+k
    vs=pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(vx),mm(vy)),mm(0.25)); hs=pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(vx),mm(vy)),mm(0.15))
    segs=[pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(mm(a[0]),mm(a[1])),pcbnew.VECTOR2I(mm(c[0]),mm(c[1])),mm(0.18)) for a,c in zip(path,path[1:])]
    worst=None
    for it in items:
        n=str(it.GetNetname())
        if n==net: continue
        pw=n.startswith("VDD") or n.startswith("VIN") or n in ("ENABLE","DEC0","SIM_VCC")
        cl=0.5 if n in("SIM_CLK","SIM_RST","SIM_IO") else 0.2 if pw else 0.15
        for L in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu):
            if not it.IsOnLayer(L): continue
            sh=it.GetEffectiveShape(L)
            vc=max(cl,1.0) if n in RF else cl
            if sh.Collide(vs,mm(vc)): return f"via vs {n} {L}"
            if L==pcbnew.F_Cu:
                for s in segs:
                    if sh.Collide(s,mm(cl)): return f"neck vs {n}"
        if it.Type()==pcbnew.PCB_VIA_T or (it.Type()==pcbnew.PCB_PAD_T and it.GetDrillSizeX()>0):
            if it.GetEffectiveHoleShape().Collide(hs,mm(0.25)): return f"hole2hole {n}"
    return "FIT"
for ref,net in (("90","GND"),):
    pad=[p for p in u.Pads() if p.GetNumber()==ref][0]; px,py=pad.GetPosition().x/1e6,pad.GetPosition().y/1e6
    res={};fits=[]
    for dx in [i*0.05 for i in range(-60,61)]:
        for dy in [i*0.05 for i in range(-60,61)]:
            vx,vy=round(px+dx,3),round(py+dy,3)
            if inkeep(vx,vy): continue
            for path in ([(px,py),(vx,vy)],[(px,py),(px,vy),(vx,vy)],[(px,py),(vx,py),(vx,vy)]):
                r=check(net,pad,vx,vy,path); res[r]=res.get(r,0)+1
                if r=="FIT": fits.append((round(math.hypot(dx,dy),2),vx,vy,path)); break
    fits=[f for f in fits if not (27.35<=f[1]<=44.65 and 26.1<=f[2]<=38.11)]; fits.sort()
    print(ref,net,(px,py),"fits",len(fits),fits[:3]); print(sorted(res.items(),key=lambda x:-x[1])[:8])
