import pcbnew,sys,json,math
from collections import defaultdict
base=pcbnew.LoadBoard("/tmp/cc/base_cd.kicad_pcb"); b=pcbnew.LoadBoard(sys.argv[1]); mm=pcbnew.FromMM
key=lambda t:(t.Type(),str(t.GetNetname()),t.GetLayer(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y)
A=set(key(t) for t in base.GetTracks()); new=[t for t in b.GetTracks() if key(t) not in A]
RF={"ANT","ANT_FIT","AUX","AUX_FIT","GPS","GNSS_ANT","GNSS_VBIAS","GNSS_VBIAS_SRC"}; SIM={"SIM_CLK","SIM_RST","SIM_IO"}
others=[x for x in list(b.GetTracks())+list(b.GetPads())]
tab=defaultdict(lambda:{"len":0,"F":0,"B":0,"In1":0,"In2":0,"vias":0}); bad=defaultdict(list)
for t in new:
    n=str(t.GetNetname())
    if t.Type()==pcbnew.PCB_VIA_T:
        tab[n]["vias"]+=1; p=t.GetPosition(); x,y=p.x/1e6,p.y/1e6
        if 27.6-0.25<=x<=44.4+0.25 and 26.35-0.25<=y<=37.86+0.25: bad[n].append(("via U1 area",x,y))
        if (0<=x<=24.2 and 20<=y<=64) or (0<=x<=29 and 26<=y<=40) or (53<=x<=60 and 12<=y<=22): bad[n].append(("via keepout",x,y))
        vs=pcbnew.SHAPE_CIRCLE(p,mm(0.25))
        for o in others:
            on=str(o.GetNetname())
            if on==n: 
                if o.Type()==pcbnew.PCB_PAD_T and o.GetEffectiveShape(pcbnew.F_Cu).Collide(vs,0) and o.GetDrillSizeX()==0: bad[n].append(("via in pad",x,y))
                continue
            if on in RF:
                for L in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu):
                    if o.IsOnLayer(L) and o.GetEffectiveShape(L).Collide(vs,mm(1.0)): bad[n].append(("via<1mm RF",on,x,y)); break
    else:
        L={"F.Cu":"F","B.Cu":"B","In1.Cu":"In1","In2.Cu":"In2"}[str(b.GetLayerName(t.GetLayer()))]
        l=t.GetLength()/1e6; tab[n]["len"]+=l; tab[n][L]+=l
        if t.GetLayer()==pcbnew.In1_Cu: bad[n].append("In1 copper")
        for (x0,y0,x1,y1,lays) in [(0,20,24.2,64,None),(0,26,29,40,(pcbnew.F_Cu,pcbnew.In1_Cu))]:
            if lays and t.GetLayer() not in lays: continue
            for p in (t.GetStart(),t.GetEnd()):
                if x0<=p.x/1e6<=x1 and y0<=p.y/1e6<=y1: bad[n].append("track in RF keepout")
# SIM clearance/parallel for new tracks vs SIM nets (same layer edge-edge)
for t in new:
    n=str(t.GetNetname())
    if t.Type()==pcbnew.PCB_VIA_T: continue
    sh=t.GetEffectiveShape(t.GetLayer())
    for o in b.GetTracks():
        on=str(o.GetNetname())
        if on==n or not ((on in SIM) or (n in SIM)) : continue
        if not o.IsOnLayer(t.GetLayer()): continue
        if o.GetEffectiveShape(t.GetLayer()).Collide(sh,mm(0.5)): bad[n].append(("SIM<0.5",on))
    for p in b.GetPads():
        on=str(p.GetNetname())
        if on!=n and ((on in SIM) or (n in SIM)) and p.IsOnLayer(t.GetLayer()) and p.GetEffectiveShape(t.GetLayer()).Collide(sh,mm(0.5)): bad[n].append(("SIM<0.5 pad",on,p.GetParent().GetReference()+"."+p.GetNumber()))
print(json.dumps({k:{a:round(v,1) for a,v in d.items()} for k,d in tab.items()}))
print(json.dumps({k:sorted(set(map(str,v)))[:6] for k,v in bad.items()}))
