import pcbnew,sys
base=pcbnew.LoadBoard("/tmp/cc/base_cd.kicad_pcb"); P=sys.argv[1]; b=pcbnew.LoadBoard(P); nets=set(sys.argv[2].split(","))
key=lambda t:(t.Type(),str(t.GetNetname()),t.GetLayer(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y)
A=set(key(t) for t in base.GetTracks()); k=0
for t in list(b.GetTracks()):
    if key(t) not in A and str(t.GetNetname()) in nets: b.Remove(t); k+=1
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(P); print("removed",k)
