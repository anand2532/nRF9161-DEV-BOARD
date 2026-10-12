import pcbnew
mm=pcbnew.FromMM
def P(x,y): return pcbnew.VECTOR2I(mm(x),mm(y))
def clear(b,net,layer,shape,skip=()):
    worst=[]
    for it in list(b.GetTracks())+list(b.GetPads()):
        n=str(it.GetNetname())
        if n==net or it in skip or not it.IsOnLayer(layer): continue
        cl=0.5 if n in("SIM_CLK","SIM_RST","SIM_IO") else 0.2 if (n.startswith(("VDD","VIN")) or n in("ENABLE","DEC0","SIM_VCC")) else 0.15
        if n=="GND": cl=0.15
        if it.GetEffectiveShape(layer).Collide(shape,mm(cl)): worst.append((n,it.GetClass()))
    return worst
