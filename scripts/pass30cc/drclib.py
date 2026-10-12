import json,subprocess,re
from collections import Counter
from pathlib import Path
BOARD="/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
def drc(dest):
    subprocess.check_call(["kicad-cli","pcb","drc","--format","json","--output",str(dest),str(BOARD)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    d=json.loads(Path(dest).read_text()); vc=Counter(v["type"] for v in d.get("violations",[]))
    nets=Counter(); gnd=0
    for it in d.get("unconnected_items",[]):
        desc=" ".join(i.get("description","") for i in it.get("items",[]))
        import re
        ns=set(re.findall(r"\[([^\]]+)\]",desc))
        if "GND" in ns: gnd+=1
        for n in ns-{"GND"}: nets[n]+=1
    return {"unconnected":len(d.get("unconnected_items",[])),"short":vc.get("shorting_items",0),"clearance":vc.get("clearance",0),
            "crossing":vc.get("tracks_crossing",0),"hole":vc.get("hole_clearance",0),"hole_to_hole":vc.get("hole_to_hole",0),
            "courtyard":vc.get("courtyards_overlap",0),"gnd_unconnected":gnd,"nongnd":dict(nets),"types":dict(vc)}
