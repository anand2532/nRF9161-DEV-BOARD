#!/usr/bin/env python3
from __future__ import annotations
import sys
import pcbnew
sys.path.insert(0, "/home/anand/kicad-projects/nRF9161-DEV-BOARD/scripts")
from final_connect import BOARD, Final
from rescue_final import pok
B = pcbnew.B_Cu

def main():
    r = Final(pcbnew.LoadBoard(BOARD)); r.collect()
    sx,sy,dx,dy=40.70,20.80,45.62,62.00
    paths=[]
    for ny in (20.45, 20.30, 20.20, 20.10, 20.00, 19.90, 19.50, 19.20, 18.80):
        for col in (27.50, 28.20, 29.00, 30.40, 31.40):
            paths.append([(sx,sy),(sx,ny),(col,ny),(col,58.80),(dx,58.80),(dx,dy)])
            paths.append([(sx,sy),(sx,ny),(col,ny),(col,40.00),(29.00,40.00),(29.00,44.00),(col,44.00),(col,58.80),(dx,58.80),(dx,dy)])
    print("P0.16 west-north")
    nclear=0
    for i,pts in enumerate(paths):
        err=pok(r,pts,B,"P0.16")
        if err is None:
            print("CLEAR", i, pts)
            nclear+=1
            if nclear>=3:
                break
        elif i<8:
            print("BLOCK", i, err)
    if nclear==0:
        print("none")

    print("nRESET shift H")
    for y in (18.20, 18.50, 18.80, 17.80, 17.20, 16.60):
        pts=[(38.25,21.80),(38.25,y),(45.68,y),(45.68,15.80)]
        err=pok(r,pts,B,"nRESET")
        print(("CLEAR" if err is None else "BLOCK"), y, err if err else pts)

if __name__=="__main__":
    main()
