import cadquery as cq
def part(name,w,l,h,cx,cy,mx,my,extra=None):
  body=cq.Workplane('XY').box(w,l,h,centered=(True,True,False)).translate((cx,cy,0))
  mark=cq.Workplane('XY').circle(min(w,l)*0.06+0.1).extrude(0.03).translate((mx,my,h))
  a=cq.Assembly(); a.add(body,name=name+'_body',color=cq.Color(0.15,0.15,0.15)); a.add(mark,name=name+'_pin1',color=cq.Color(0.9,0.9,0.9))
  if extra: a.add(extra[0],name=name+'_x',color=cq.Color(*extra[1]))
  a.save(name+'.step')
part('nRF9161_LGA_16.0x10.5mm_placeholder',16.0,10.5,1.04,0,0,-7.0,4.3)
part('TI_USON-8_2.1x1.6mm_placeholder',2.1,1.6,0.6,0,0,-0.65,-0.45)
part('JAE_SF72S006_placeholder',11.3,14.45,1.5,-0.98,-2.115,-2.54,0.5)
act=cq.Workplane('XY').box(1.2,0.8,0.25,centered=(True,True,False)).translate((0,0,0.55))
part('CK_KXT3_placeholder',3.6,2.1,0.55,0,0,-1.5,0.8,extra=(act,(0.8,0.8,0.8)))
