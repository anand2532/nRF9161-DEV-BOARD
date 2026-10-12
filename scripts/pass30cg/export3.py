import pcbnew,sys
RIP=set(sys.argv[2].split(",")) if len(sys.argv)>2 and sys.argv[2] else set()
b=pcbnew.LoadBoard("/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb")
mm=pcbnew.FromMM
for t in b.GetTracks():
    t.SetLocked(str(t.GetNetname()) not in RIP)
ns=b.GetDesignSettings().m_NetSettings
d=ns.GetDefaultNetclass(); d.SetTrackWidth(mm(0.18)); d.SetViaDiameter(mm(0.5)); d.SetViaDrill(mm(0.3)); d.SetClearance(mm(0.15))
p=ns.GetNetclasses()["POWER"]; p.SetClearance(mm(0.2))
cu=pcbnew.LSET.AllCuMask()
def ko(x0,y0,x1,y1,layers,vias=True,tracks=True,name=""):
    z=pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetLayerSet(layers)
    z.SetDoNotAllowVias(vias); z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    o=z.Outline(); o.NewOutline()
    for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]: o.Append(mm(x),mm(y))
    o.Outline(0).SetClosed(True); z.SetZoneName(name); b.Add(z)
ko(0,20,24.2,64,cu,name="RF")
l=pcbnew.LSET(); l.AddLayer(pcbnew.F_Cu); l.AddLayer(pcbnew.In1_Cu); ko(0,26,29,40,l,name="RF2")
l=pcbnew.LSET(); l.AddLayer(pcbnew.In2_Cu); ko(0,20,29,64,l,name="RF_IN2")
l=pcbnew.LSET(); l.AddLayer(pcbnew.In2_Cu); ko(27.6,26.35,44.4,37.86,l,name="U1_IN2")
for (a,b_,c,d) in ((0,0,120,0.6),(0,79.4,120,80),(0,0,0.6,80),(119.4,0,120,80)): ko(a,b_,c,d,cu,name="EDGE")
ko(53,12,60,22,cu,vias=True,tracks=False,name="NECKV")
l=pcbnew.LSET(); l.AddLayer(pcbnew.In2_Cu); ko(53,12,60,22,l,name="NECK")
l=pcbnew.LSET(); l.AddLayer(pcbnew.B_Cu); ko(81.8,44.2,97.3,45.0,l,name="POCKET")
u=b.FindFootprintByReference("U1"); c=u.GetBoundingBox(False,False)
ko(c.GetX()/1e6,c.GetY()/1e6,c.GetRight()/1e6,c.GetBottom()/1e6,cu,vias=True,tracks=False,name="U1CY")
print("U1 courtyard",c.GetX()/1e6,c.GetY()/1e6,c.GetRight()/1e6,c.GetBottom()/1e6)
print(pcbnew.ExportSpecctraDSN(b,sys.argv[1]))

import re
p=sys.argv[1]; d=open(p).read()
d=d.replace('(via "Via[0-3]_500:300_um" "Via[0-3]_800:400_um" "Via[0-3]_600:300_um")','(via "Via[0-3]_500:300_um")')
d=d.replace('(use_via "Via[0-3]_800:400_um")','(use_via "Via[0-3]_500:300_um")').replace('(use_via "Via[0-3]_600:300_um")','(use_via "Via[0-3]_500:300_um")')
for LL in ("In1.Cu",): d=d.replace("(layer "+LL+"\n      (type signal)","(layer "+LL+"\n      (type power)",1)
d=d.replace("(width 400)\n        (clearance 200)","(width 300)\n        (clearance 200)")
m=re.search(r"\(class kicad_default (.*?)\n      \(circuit",d,re.S)
names=m.group(1).split(); SIM={"SIM_CLK","SIM_RST","SIM_IO"}; RFX={"GNSS_VBIAS","GNSS_VBIAS_SRC"}; names=[n for n in names if n not in SIM|RFX]; PW={"ENABLE","DEC0","SIM_VCC"}
d=d[:m.start(1)]+" ".join(n for n in names if n not in PW)+d[m.end(1):]
d=d.replace("(class POWER ","(class POWER "+" ".join(sorted(PW))+" ")
cls=lambda nm,nets,cl:"    (class "+nm+" "+nets+"\n      (circuit\n        (use_via \"Via[0-3]_500:300_um\")\n      )\n      (rule\n        (width 180)\n        (clearance "+cl+")\n      )\n    )\n"
d=re.sub(r"    \(class RF_50OHM ([^\n(]*)\n",lambda m:"    (class RF_50OHM "+m.group(1).strip()+" GNSS_VBIAS GNSS_VBIAS_SRC\n",d,1)
d=d.replace("    (class POWER ",cls("SIM","SIM_CLK SIM_IO SIM_RST","500")+"    (class POWER ",1)
i=d.index("(class RF_50OHM"); j=d.index("(clearance 150)",i); d=d[:j]+"(clearance 1000)"+d[j+15:]
open(p,"w").write(d); print("dsn ok")
