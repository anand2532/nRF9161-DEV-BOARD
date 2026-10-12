import pcbnew,sys,math
P=sys.argv[1]; b=pcbnew.LoadBoard(P); mm=pcbnew.FromMM
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
gnd=b.FindNet("GND"); RF={"ANT","ANT_FIT","AUX","AUX_FIT","GPS","GNSS_ANT","GNSS_VBIAS","GNSS_VBIAS_SRC"}
zF=[z for z in b.Zones() if str(z.GetNetname())=="GND" and z.IsOnLayer(pcbnew.F_Cu) and not z.GetIsRuleArea()][0]
p=zF.GetFilledPolysList(pcbnew.F_Cu); sl=None; st=None
for i in range(p.OutlineCount()):
    bb=p.Outline(i).BBox(); x,y=bb.GetX()/1e6,bb.GetY()/1e6
    if abs(x-36.6)<0.15 and abs(y-36.8)<0.15: sl=i
    if abs(x-45.9)<0.15 and abs(y-28.3)<0.15: st=i
print("sliver",sl,"stitch",st)
# keepout over sliver
if sl is not None:
  o=p.Outline(sl); z=pcbnew.ZONE(b); z.SetIsRuleArea(True); l=pcbnew.LSET(); l.AddLayer(pcbnew.F_Cu); z.SetLayerSet(l)
  z.SetDoNotAllowZoneFills(True) if hasattr(z,"SetDoNotAllowZoneFills") else z.SetDoNotAllowCopperPour(True)
  z.SetDoNotAllowVias(False); z.SetDoNotAllowTracks(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
  ol=z.Outline(); ol.NewOutline()
  for k in range(o.PointCount()): ol.Append(o.CPoint(k))
  z.SetZoneName("pass30cd_sliver_noFill"); b.Add(z)
# stitch vias
poly=p.Outline(st); items=list(b.GetTracks())+list(b.GetPads()); placed=[]
bb=poly.BBox()
for yy in range(int(bb.GetY()), int(bb.GetBottom()), mm(0.1)):
  for xx in range(int(bb.GetX()), int(bb.GetRight()), mm(0.1)):
    c=pcbnew.VECTOR2I(xx,yy); x,y=xx/1e6,yy/1e6
    if 27.35<=x<=44.65 and 26.1<=y<=38.11: continue
    if (x<=29.25 and 25.75<=y<=40.25) or (x<=24.45 and 19.75<=y<=64.25): continue
    if any(math.hypot(x-a,y-bq)<2.0 for a,bq in placed): continue
    # fully inside fragment with 0.25 margin
    if not poly.PointInside(c) or False: continue
    vs=pcbnew.SHAPE_CIRCLE(c,mm(0.25)); hs=pcbnew.SHAPE_CIRCLE(c,mm(0.15)); ok=True
    for it in items:
        n=str(it.GetNetname())
        for L in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu):
            if not it.IsOnLayer(L): continue
            if n=="GND" and L!=pcbnew.F_Cu: continue
            cl=1.0 if n in RF else 0.5 if n in("SIM_CLK","SIM_RST","SIM_IO") else 0.2 if (n.startswith(("VDD","VIN")) or n in("ENABLE","DEC0","SIM_VCC")) else 0.15
            if n=="GND": cl=0
            if n!="GND" and it.GetEffectiveShape(L).Collide(vs,mm(cl)): ok=False;break
        if not ok: break
        if it.Type()==pcbnew.PCB_VIA_T or (it.Type()==pcbnew.PCB_PAD_T and it.GetDrillSizeX()>0):
            if it.GetEffectiveHoleShape().Collide(hs,mm(0.25)): ok=False;break
    # In2 VDD_nRF plane: via is GND, fine (antipad)
    if ok:
        v=pcbnew.PCB_VIA(b); v.SetPosition(c); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetWidth(mm(0.5)); v.SetDrill(mm(0.3)); v.SetNet(gnd); b.Add(v); placed.append((x,y)); items.append(v)
print("stitch vias",placed)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(P)
