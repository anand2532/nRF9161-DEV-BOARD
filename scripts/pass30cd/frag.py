import pcbnew,sys,json
b=pcbnew.LoadBoard(sys.argv[1])
if len(sys.argv)>2: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
out={}
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    for l in z.GetLayerSet().Seq():
        p=z.GetFilledPolysList(l); n=p.OutlineCount()
        areas=sorted([p.Outline(i).Area()/1e12 - sum(p.Hole(i,j).Area()/1e12 for j in range(p.HoleCount(i))) for i in range(n)],reverse=True)
        bbs=[]
        for i in range(n):
            bb=p.Outline(i).BBox(); bbs.append((round(abs(areas[0]) if 0 else 0,1),))
        out[f"{z.GetNetname()} {b.GetLayerName(l)}"]={"pieces":n,"area":round(sum(areas),1),"areas":[round(a,1) for a in areas]}
print(json.dumps(out))
