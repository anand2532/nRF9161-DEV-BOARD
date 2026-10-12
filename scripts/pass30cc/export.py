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
if not __import__("os").environ.get("IN2"): d=d.replace("(layer In2.Cu\n      (type signal)","(layer In2.Cu\n      (type power)",1)
d=d.replace("(width 400)\n        (clearance 200)","(width 300)\n        (clearance 200)")
m=re.search(r"\(class kicad_default (.*?)\n      \(circuit",d,re.S)
names=m.group(1).split(); PW={"ENABLE","DEC0","SIM_VCC","GNSS_VBIAS","GNSS_VBIAS_SRC"}
d=d[:m.start(1)]+" ".join(n for n in names if n not in PW)+d[m.end(1):]
d=d.replace("(class POWER ","(class POWER "+" ".join(sorted(PW))+" ")
open(p,"w").write(d); print("dsn ok")
