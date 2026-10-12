import subprocess,json,shutil,re
def OK(desc):
    n=re.search(r"\[([^\]]+)\]",desc).group(1)
    pass
    if n=="VDD_GPIO": return True
    pass
    return False
skipped=[]
P="/workspace/kicad-projects/nRF9161-DEV-BOARD/nRF9161-DEV-BOARD.kicad_pcb"
def drc():
    o=subprocess.run(["python3","/tmp/cc/drcrun.py","/tmp/cc/dg.json"],capture_output=True,text=True,cwd="/tmp/cc").stdout.strip().splitlines()[-1]
    return json.loads(o),json.load(open("/tmp/cc/dg.json"))
def sig(r): return (r["nongnd"],r["gnd_unconnected"],r["short"],r["clearance"],r["crossing"],r["hole"],r["hole_to_hole"])
r0,d=drc(); base=sig(r0); removed=[]; kept=[]; tried=set()
while True:
    cand=[(v["type"],i) for v in d["violations"] if v["type"] in("via_dangling","track_dangling") for i in v["items"] if i["uuid"] not in tried and OK(i["description"])]
    if not cand: break
    typ,i=cand[0]; tried.add(i["uuid"])
    shutil.copy(P,"/tmp/cc/dg_bak.kicad_pcb")
    subprocess.run(["python3","/tmp/cc/rmuuid.py",P,i["uuid"]],capture_output=True)
    r,d2=drc()
    if sig(r)[0]==base[0] and sig(r)[1]<=base[1] and sig(r)[2:]==base[2:] or (r["nongnd"]==base[0] and r["gnd_unconnected"]<=base[1] and r["short"]==0 and r["clearance"]==0 and r["crossing"]==0 and r["hole"]==0 and r["hole_to_hole"]<=1):
        removed.append((typ,i["description"],i["pos"])); d=d2; base=sig(r)
    else:
        shutil.copy("/tmp/cc/dg_bak.kicad_pcb",P); kept.append((typ,i["description"],i["pos"],"would change: "+json.dumps({k:v for k,v in r["nongnd"].items() if v!=base[0].get(k)})+" gnd "+str(r["gnd_unconnected"])))
skipped=[(v["type"],i["description"],i["pos"]) for v in d["violations"] if v["type"] in("via_dangling","track_dangling") for i in v["items"] if not OK(i["description"])]
json.dump({"removed":removed,"kept":kept,"skipped_locked":skipped},open("/tmp/cc/dangling_result.json","w"),indent=0)
print(len(skipped),len(removed),len(kept),sum(1 for x in removed if x[0]=="via_dangling"),sum(1 for x in removed if x[0]=="track_dangling"))
