"""DriveTTO continuous endpoint-to-trajectory explainer (NAV1 Full schematic).

All geometry, endpoint samples and utility colors are illustrations. Real benchmark
clips are appended separately. The animation does not execute or simulate a planner.
"""
from pathlib import Path
from functools import lru_cache
import argparse, hashlib, json, math, subprocess, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W,H,FPS,DURATION=1280,720,24,168
C={'bg':'#08141f','panel':'#102331','road':'#243847','edge':'#81939b',
   'text':'#eef5f8','muted':'#a5bbc6','cyan':'#52d9ec','gold':'#f5bf69',
   'green':'#64e4b2','red':'#ff827d','purple':'#b1a3f7','line':'#314b5a'}
PHASES=[(0,18,'SMALL MARGINS'),(18,58,'ENDPOINT SEARCH'),(58,88,'TWO PLANNERS'),
        (88,116,'LOCAL REFINEMENT'),(116,142,'FUSION & SELECTION'),(142,168,'COMPLETE MOTION')]
CAPS=[
 (0,7,'In a tight corridor, a plausible centerline still leaves little room for the vehicle.'),
 (7,12,'A small lateral shift can turn clearance into overlap. The vehicle footprint matters.'),
 (12,18,'A small forward shift changes where the vehicle meets crossing traffic.'),
 (18,25,'DriveTTO starts with endpoint requests, completed through a native parent trajectory.'),
 (25,33,'Score the complete path. Store its utility at the endpoint that the path actually reaches.'),
 (33,43,'Nearby achieved states guide the next requests toward a promising region.'),
 (43,51,'The archive uses eight neighbors in position, heading and speed. This view projects XY.'),
 (51,58,'Each new request produces another complete path, which is evaluated before updating the archive.'),
 (58,67,'The accepted endpoint plan and a second planner provide different complete motions.'),
 (67,77,'Bounded interpolation and geometric refinement establish one shared trajectory center.'),
 (77,88,'Small longitudinal, lateral and timing changes refine the path around this center.'),
 (88,98,'Proposals from both frozen planners contribute alternative local shapes.'),
 (98,108,'A control branch transfers a bounded change between two rollouts onto the same center.'),
 (108,116,'Zero control perturbation preserves the center. Both branches retain a complete trajectory.'),
 (116,125,'Proposal and control outputs are combined at matching future timestamps.'),
 (125,134,'Smooth temporal weights allow the early and late parts to use different branch contributions.'),
 (134,142,'Compare each complete candidate with its reference. Configured dual-scoring stages use both heads.'),
 (142,151,'An admitted update replaces the reference; otherwise the reference is kept exactly.'),
 (151,160,'Endpoint search finds promising motions; local refinement adjusts their geometry and timing.'),
 (160,168,'The same complete motion links the endpoint, the narrow passage and the crossing interaction.')]

def clamp(x):return min(1.,max(0.,x))
def ease(x):x=clamp(x);return x*x*(3-2*x)
def ramp(t,a,b):return ease((t-a)/(b-a))
def rgb(s):return s if isinstance(s,tuple) else tuple(int(s[i:i+2],16) for i in (1,3,5))
def mix(a,b,f):return tuple(round(x+(y-x)*f) for x,y in zip(rgb(a),rgb(b)))
@lru_cache(None)
def font(n,b=False):
 for p in [Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'),Path('C:/Windows/Fonts')/('arialbd.ttf' if b else 'arial.ttf')]:
  if p.is_file():return ImageFont.truetype(str(p),n)
 raise FileNotFoundError('font')
def txt(d,xy,s,n=20,col=None,b=False,anchor=None):d.text(xy,s,font=font(n,b),fill=col or C['text'],anchor=anchor)
def wrap(d,s,x,y,width,n=22,col=None,b=False,spacing=8):
 line=''
 for word in s.split():
  test=(line+' '+word).strip()
  if d.textlength(test,font=font(n,b))>width and line:
   txt(d,(x,y),line,n,col,b);y+=n+spacing;line=word
  else:line=test
 if line:txt(d,(x,y),line,n,col,b)
 return y+n
def dot(d,p,r,col,outline=None,width=2):d.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),fill=col,outline=outline,width=width)
def arrow(d,p,q,col,width=2):
 d.line((p,q),fill=col,width=width);a=math.atan2(q[1]-p[1],q[0]-p[0]);sz=7
 d.polygon([q,(q[0]-sz*math.cos(a-.5),q[1]-sz*math.sin(a-.5)),(q[0]-sz*math.cos(a+.5),q[1]-sz*math.sin(a+.5))],fill=col)
def center(x):return 1.4*np.sin(np.asarray(x)/13)+.045*np.asarray(x)
def pos(x,y):return (74+14.3*float(x),432-30.*float(y))
def map_points(x,y):return [pos(a,b) for a,b in zip(x,y)]
X=np.linspace(0,49,150)
def trajectory(kind='reference',endx=46.,endy=-.15):
 s=np.linspace(0,1,150);x=s*endx
 base=.20*np.exp(-((x-22)/6)**2)
 if kind=='reference':off=.45*np.exp(-((x-22)/6)**2)+.42*(x/49)**2
 elif kind=='endpoint':off=base-.16*np.exp(-((x-22)/4)**2)+endy*s*s
 elif kind=='planner2':off=-.65*np.exp(-((x-22)/9)**2)-.45*s*s
 elif kind=='geometry':off=-.25*np.exp(-((x-22)/7)**2)-.20*s*s
 elif kind=='proposal':off=-.40*np.exp(-((x-22)/5)**2)-.14*s*s
 elif kind=='control':off=-.25*np.exp(-((x-22)/8)**2)-.37*s*s
 elif kind=='final':
  a=trajectory('proposal',endx,endy);c=trajectory('control',endx,endy);w=s*s*(3-2*s)
  return x,a[1]*(1-w)+c[1]*w
 else:raise ValueError(kind)
 return x,center(x)+off
def blend(a,b,p):return (a[0]*(1-p)+b[0]*p,a[1]*(1-p)+b[1]*p)
def path(d,xy,col,width=3,portion=1,poses=False,dashed=False):
 points=map_points(*xy);n=max(2,int(len(points)*clamp(portion)));points=points[:n]
 if dashed:
  for i in range(0,n-1,6):d.line(points[i:min(i+4,n)],fill=col,width=width)
 else:d.line(points,fill=col,width=width,joint='curve')
 if poses:
  for j in np.linspace(0,n-1,9).astype(int):dot(d,points[j],3,col)
 return points[-1]
def vehicle(d,x,y,col,scale=1,angle=0,outline=None,mapper=pos):
 # Vehicle is a 4.6 m x 1.85 m rectangle, headed along the road.
 c,s=math.cos(angle),math.sin(angle)
 pts=[mapper(x+c*a-s*b,y+s*a+c*b) for a,b in [(-2.3*scale,-.925*scale),(2.3*scale,-.925*scale),(2.3*scale,.925*scale),(-2.3*scale,.925*scale)]]
 d.polygon(pts,fill=col,outline=outline or C['bg']);d.line(pts+[pts[0]],fill=outline or C['bg'],width=2)
 a=mapper(x+.5*scale,y-.7*scale);b=mapper(x+1.25*scale,y+.7*scale)
 d.line((a,b),fill=mix(col,'#ffffff',.5),width=3)
def world_base():
 im=Image.new('RGB',(W,H),C['bg']);d=ImageDraw.Draw(im)
 d.rounded_rectangle((26,144,839,594),radius=18,fill=C['panel'])
 d.rounded_rectangle((857,144,1254,594),radius=18,fill=C['panel'])
 xx=np.linspace(-2,52,200);yy=center(xx)
 outer=map_points(xx,yy+4.8)+map_points(xx[::-1],(yy-3.1)[::-1]);d.polygon(outer,fill='#1b363b')
 road=map_points(xx,yy+4.3)+map_points(xx[::-1],(yy-2.0)[::-1]);d.polygon(road,fill=C['road'])
 for offset in [-2,4.3]:d.line(map_points(xx,yy+offset),fill=C['edge'],width=3)
 for i in range(0,len(xx)-7,12):d.line(map_points(xx[i:i+7],yy[i:i+7]+1.1),fill='#8a9a9f',width=2)
 # Pavement blocks, trees and subtle distance grid maintain scene identity.
 for j in range(5):
  x=145+j*133;y=219-8*j
  d.rounded_rectangle((x,y,x+56,y+33),6,fill='#243945',outline='#3c5261')
 for j in range(4):
  dot(d,(111+j*192,555),15,'#234a45');dot(d,(105+j*192,549),9,'#306457')
 vehicle(d,22,float(center(22))+1.95,'#8297a4',1.02)
 txt(d,(336,269),'parked vehicle',15,C['muted'])
 txt(d,(595,260),'crossing traffic',15,C['muted'])
 txt(d,(47,163),'ONE SCENE  /  ONE CONTINUOUS REFINEMENT',14,C['muted'],True)
 txt(d,(48,564),'0',12,C['muted']);txt(d,(746,564),'forward distance',12,C['muted'])
 return im
BASE=world_base()
RNG=np.random.default_rng(10631)
SAMPLES=[]
for i in range(54):
 if i<18:x,y=RNG.uniform(39,50),RNG.uniform(-2,1.9)
 elif i<36:x,y=RNG.normal(45.7,1.8),RNG.normal(-.2,.7)
 else:x,y=RNG.normal(46.,.8),RNG.normal(-.25,.36)
 x=float(np.clip(x,39,50));y=float(np.clip(y,-2,1.9))
 # Synthetic path-dependent utility for illustration, never reported as a result.
 u=float(np.clip(np.exp(-((x-46)/4.2)**2-((y+.25)/1.1)**2)*.90+.04*np.sin(x),0,1))
 SAMPLES.append((x,y,u))
def ucolor(u):return mix('#455477','#71edbc',clamp(u))
@lru_cache(None)
def heat(count):
 a=np.array(SAMPLES[:max(1,count)]);xx,yy=np.meshgrid(np.linspace(39,50,176),np.linspace(1.9,-2,144));grid=np.stack([xx,yy],-1)
 dist=((grid[...,None,:]-a[None,None,:,:2])/np.array([2.,.6]))**2;dist=dist.sum(-1)
 k=min(8,len(a));ix=np.argsort(dist,axis=-1)[...,:k];ds=np.take_along_axis(dist,ix,-1);weights=np.exp(-ds/2);weights/=np.maximum(weights.sum(-1,keepdims=True),1e-12)
 u=(weights*a[ix,2]).sum(-1);rgb0=np.array(rgb('#233348'));rgb1=np.array(rgb('#4bb38b'))
 arr=(rgb0+(rgb1-rgb0)*u[...,None]).astype(np.uint8)
 return Image.fromarray(arr).resize((352,288),Image.Resampling.BILINEAR)
def endpoint_panel(im,d,t):
 txt(d,(878,163),'TERMINAL UTILITY ARCHIVE',16,C['green'],True)
 n=min(54,max(0,int((t-20)/.61)))
 if n:im.paste(heat(n),(879,207))
 else:d.rectangle((879,207,1231,495),fill='#152b3a')
 def hp(x,y):return (879+(x-39)/11*352,207+(1.9-y)/3.9*288)
 for x,y,u in SAMPLES[:n]:dot(d,hp(x,y),4,ucolor(u),C['bg'],1)
 if n>20:
  best=sorted(SAMPLES[:n],key=lambda q:q[2])[-8:];p=np.mean(np.array(best)[:,:2],0);q=hp(*p)
  rad=54-22*ramp(t,35,56);d.ellipse((q[0]-rad,q[1]-rad*.9,q[0]+rad,q[1]+rad*.9),outline=C['gold'],width=2)
  txt(d,(889,217),'promising region',15,C['gold'],True)
 if n>36:
  point=hp(46,-.25);nearest=sorted(SAMPLES[:n],key=lambda q:((q[0]-46)/2)**2+((q[1]+.25)/.6)**2)[:8]
  for x,y,u in nearest:d.line((point,hp(x,y)),fill='#d6c68c',width=1)
  dot(d,point,7,None,C['gold'],2)
 for k in range(100):d.line((879+k*3.1,510,882+k*3.1,510),fill=ucolor(k/99),width=8)
 txt(d,(879,523),'lower',13,C['muted']);txt(d,(1192,523),'higher',13,C['green'])
 txt(d,(879,548),f'{n:02d} evaluated full paths',17,b=True)
 txt(d,(879,574),'XY view  |  heading + speed also indexed',13,C['muted'])
 txt(d,(882,189),'lateral',12,C['muted']);txt(d,(1149,189),'longitudinal',12,C['muted'])

def closeup(im,d,t,mode='lateral'):
 txt(d,(879,163),'VEHICLE-FOOTPRINT CLOSE-UP',15,C['gold'],True)
 zoom=Image.new('RGB',(354,273),'#263c4b');z=ImageDraw.Draw(zoom)
 mx=lambda x,y:(175+(x-22)*43,174-(y-float(center(22)))*55)
 z.line((0,263,354,263),fill='#9aabb2',width=3)
 vehicle(z,22,float(center(22))+1.95,'#8297a4',1.02,mapper=mx)
 yy=float(center(22))-.1
 if mode=='compare':
  off=.45-.8*ramp(t,143,150)
  vehicle(z,22,float(center(22))+off,C['green'],mapper=mx,outline=C['text'])
  txt(d,(879,496),'Local shape changes clearance',18,C['green'],True)
  wrap(d,'Compare complete vehicle footprints along the refined path.',879,531,350,18,C['muted'])
 elif mode=='lateral':
  shift=.35*ramp(t%10,2,6)
  vehicle(z,22,yy+shift,mix(C['green'],C['red'],clamp(shift/.35)),mapper=mx,outline=C['text'])
  arrow(z,mx(25,yy),mx(25,yy+.35),C['gold'],3)
  txt(d,(879,496),'+0.35 m sideways',21,C['gold'],True)
  wrap(d,'A small shift uses the remaining clearance.',879,534,352,18,C['muted'])
 else:
  # A second rectangular footprint crosses the longitudinal path.
  vehicle(z,24.8,float(center(22))-1.2,C['red'],.75,angle=math.pi/2,mapper=mx)
  shift=.55*ramp(t%10,2,6)
  vehicle(z,20.8+shift,yy,C['green'],mapper=mx,outline=C['text'])
  arrow(z,mx(20.8,yy-1.3),mx(21.35,yy-1.3),C['gold'],3)
  txt(d,(879,496),'Forward position + arrival time',18,C['gold'],True)
  wrap(d,'The same path shape can meet traffic at a different time.',879,531,350,18,C['muted'])
 im.paste(zoom,(878,205))

def local_detail(d,a,b,cur,labels):
 d.rounded_rectangle((260,461,810,580),12,fill='#132a36',outline='#55727e',width=1)
 txt(d,(274,470),'LOCAL PATH DETAIL  /  MAGNIFIED LATERAL SEPARATION',12,C['muted'],True)
 for xy,col in [(a,C['cyan']),(b,C['gold']),(cur,C['green'])]:
  xx=np.linspace(16,28,80);yy=np.interp(xx,*xy)-center(xx)
  pp=[(280+(x-16)*42,515-y*40) for x,y in zip(xx,yy)]
  d.line(pp,fill=col,width=3)
 for i,(name,col) in enumerate(zip(labels,[C['cyan'],C['gold'],C['green']])):txt(d,(274+i*174,558),name,12,col)

def refinement_panel(d,t):
 txt(d,(879,163),'TWO FROZEN PLANNERS',17,C['green'],True)
 for j,(name,col) in enumerate([('ChainFlow',C['cyan']),('DrivoR',C['gold'])]):
  y=209+j*67;d.rounded_rectangle((879,y,1231,y+48),9,fill='#193442',outline=col,width=2)
  txt(d,(895,y+12),name,22,col,True);txt(d,(1141,y+15),'frozen',15,C['muted'])
 arrow(d,(1055,329),(1055,355),C['muted'])
 if t<88:
  txt(d,(879,369),'One shared trajectory center',20,b=True)
  wrap(d,'Endpoint plan + bounded interpolation + geometric search',879,408,350,20,C['muted'])
  for j,s in enumerate(['lateral position','longitudinal position','time scale']):
   y=494+26*j;txt(d,(882,y),s,16,C['muted']);d.line((1091,y+11,1222,y+11),fill=C['line'],width=4)
   dot(d,(1154+31*math.sin(t*.7+j),y+11),5,C['green'])
 elif t<116:
  txt(d,(879,365),'Local proposal + control branches',18,b=True)
  wrap(d,'Transfer the change between two control rollouts onto the stored center.',879,403,350,19,C['muted'])
  txt(d,(879,485),'c = center + bounded rollout change',15,C['green'])
  txt(d,(879,521),'NAV1 bound: 0.8 m / 0.06 rad',17,b=True)
  txt(d,(879,558),'Zero perturbation = exact center',15,C['muted'])
 else:
  txt(d,(879,366),'REFERENCE-RELATIVE SCORING',16,b=True)
  txt(d,(879,406),'candidate + reference',21,C['text'],True)
  txt(d,(879,438),'fixed slots / same proposal bank',16,C['muted'])
  for j,(name,col) in enumerate([('ChainFlow gain',C['cyan']),('DrivoR gain',C['gold'])]):
   y=478+j*32;txt(d,(879,y),name,16,col);d.line((1058,y+11,1221,y+11),fill=C['line'],width=6)
   d.line((1058,y+11,1125+45*math.sin(t*.35+j)**2,y+11),fill=col,width=6)
  txt(d,(879,550),'Minimum gain in configured stages',15,C['muted'])
  txt(d,(879,572),'Predicted gains are not safety guarantees.',13,C['muted'])

def draw_frame(t):
 im=BASE.copy();d=ImageDraw.Draw(im)
 phase=next(i for i,(a,b,s) in enumerate(PHASES) if a<=t<b)
 titles=['Small changes, different clearances','Search where complete paths can end','Turn a promising endpoint into a precise path',
 'Refine shape and motion around one center','Combine useful parts along the horizon','A complete path through the whole scene']
 txt(d,(36,22),'DriveTTO',29,C['green'],True);txt(d,(227,29),'ENDPOINT SEARCH  →  PRECISE TRAJECTORY REFINEMENT',17,C['muted'],True)
 txt(d,(36,66),titles[phase],29,b=True)
 for i,(a,b,label) in enumerate(PHASES):
  x=36+i*205;d.line((x,126,x+185,126),fill=C['line'],width=3)
  f=clamp((t-a)/(b-a));d.line((x,126,x+185*f,126),fill=C['green'],width=3)
  txt(d,(x,107),label,12,C['green'] if i==phase else C['muted'],True)
 ref=trajectory('reference');end=trajectory('endpoint');p2=trajectory('planner2');geo=trajectory('geometry');prop=trajectory('proposal');ctrl=trajectory('control');final=trajectory('final')
 # Crossing actor retains the same identity throughout the demonstration.
 crossing_y=float(center(36))+2.45+.25*math.sin(t*.15)
 vehicle(d,36,crossing_y,'#a4aeb8',.85,angle=-.65)
 if t<18:
  path(d,ref,C['gold'],4,poses=True)
  for sign in [-1,1]:path(d,(ref[0],ref[1]+sign*.35),mix(C['panel'],C['red'],.60),2,dashed=True)
  x=22 if t<12 else 34.5;yy=float(np.interp(x,*ref));vehicle(d,x,yy,C['gold'],outline=C['text'])
  closeup(im,d,t,'lateral' if t<12 else 'time')
  d.rectangle((330,326,449,431),outline=C['gold'],width=2);d.line((449,326,850,226),fill='#698184',width=1)
 elif t<58:
  endpoint_panel(im,d,t);path(d,ref,'#627685',2,dashed=True)
  n=min(54,max(0,int((t-20)/.61)))
  for x,y,u in SAMPLES[:n]:
   xy=trajectory('endpoint',x,y);dot(d,pos(x,float(center(x))+y),3,ucolor(u))
   if n<7 or u>.82:path(d,xy,mix(C['panel'],ucolor(u),.42),1)
  if n:
   x,y,u=SAMPLES[n-1];xy=trajectory('endpoint',x,y)
   # Each new full curve is traced before its sample is visually emphasized.
   tail=path(d,xy,ucolor(u),3,ramp((t-20)%.61,0,.5));dot(d,tail,5,ucolor(u))
   req=pos(x+.6,float(center(x))+y+.23);dot(d,req,7,None,C['gold'],2)
   arrow(d,req,pos(x,float(center(x))+y),C['gold'])
  if t>50:path(d,end,C['green'],5,ramp(t,50,55),poses=True)
  txt(d,(48,198),'complete path → achieved state → utility archive',18,C['green'],True)
  txt(d,(49,531),'○ requested endpoint      ● achieved endpoint',15,C['muted'])
 elif t<88:
  refinement_panel(d,t);path(d,end,C['cyan'],4,poses=True);path(d,p2,C['gold'],4,ramp(t,59,65),poses=True)
  cur=blend(end,p2,.40*ramp(t,67,76)) if t<77 else blend(blend(end,p2,.4),geo,ramp(t,77,86))
  path(d,cur,C['green'],5,poses=True);vehicle(d,22,float(np.interp(22,*cur)),C['green'],outline=C['text'])
  txt(d,(49,198),'ChainFlow endpoint plan',17,C['cyan'],True);txt(d,(49,226),'DrivoR proposal',17,C['gold'],True)
  if t>74:
   for x in [14,22,34]:
    p=pos(x,float(np.interp(x,*cur)));arrow(d,(p[0],p[1]+19),(p[0],p[1]-19),C['green'])
  local_detail(d,end,p2,cur,['endpoint plan','second planner','refined center'])
 elif t<116:
  refinement_panel(d,t);path(d,geo,'#7b909c',3,dashed=True)
  for k in range(7):
   alpha=k/12;draft=blend(geo,p2,alpha);path(d,draft,mix(C['panel'],C['gold'],.22),1)
  path(d,prop,C['cyan'],4,ramp(t,88,97),poses=True)
  path(d,ctrl,C['purple'],4,ramp(t,98,107),poses=True)
  txt(d,(49,198),'proposal branch',17,C['cyan'],True);txt(d,(49,226),'control branch',17,C['purple'],True)
  x=22;vehicle(d,x,float(np.interp(x,*geo)),'#7b909c',outline=C['muted'])
  if t>101:
   p=pos(x,float(np.interp(x,*geo)));q=pos(x,float(np.interp(x,*ctrl)));arrow(d,p,q,C['purple'],3)
  local_detail(d,prop,ctrl,geo,['proposal branch','control branch','shared center'])
 elif t<142:
  refinement_panel(d,t);path(d,prop,C['cyan'],3,poses=True);path(d,ctrl,C['purple'],3,poses=True)
  cur=blend(prop,final,ramp(t,116,133));path(d,cur,C['green'],5,poses=True)
  tick=(t-116)/26;idx=int(clamp(tick)*149)
  for xy,col in [(prop,C['cyan']),(ctrl,C['purple']),(cur,C['green'])]:dot(d,pos(xy[0][idx],xy[1][idx]),6,col,C['text'],1)
  txt(d,(49,198),'matched timestamps',18,C['green'],True)
  local_detail(d,prop,ctrl,cur,['proposal branch','control branch','temporal fusion'])
 else:
  closeup(im,d,t,'compare' if t<151 else 'time')
  path(d,ref,'#b08f68',2,dashed=True);path(d,final,C['green'],5,poses=True)
  run=ramp(t,144,165);x=1+44*run;y=float(np.interp(x,*final))
  for xx in [9,16,22,28,35,42]:
   vehicle(d,xx,float(np.interp(xx,*final)),mix(C['road'],C['green'],.20),outline='#49695e')
  path(d,final,C['green'],5,poses=True);vehicle(d,x,y,C['green'],outline=C['text'])
  txt(d,(49,198),'endpoint region → local refinement → retained complete path',17,C['green'],True)
  txt(d,(49,531),'8 poses at 0.5 s intervals  |  the entire motion is compared',16,C['muted'])
 vehicle(d,0,0,C['cyan'],outline=C['text'])
 # Stable subtitle strip; all details stay in one animated scene.
 caption=next(s for a,b,s in CAPS if a<=t<b)
 wrap(d,caption,38,615,1200,24,C['text'],False,5)
 txt(d,(38,694),'NAV1 Full  ·  Schematic scene, utility and perturbations  ·  Frozen models',13,C['muted'])
 txt(d,(1240,694),f'{int(t)//60}:{int(t)%60:02d} / 2:48',13,C['muted'],anchor='ra')
 return im

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stamp(t):return f'{int(t)//3600:02}:{int(t)//60%60:02}:{int(t)%60:02}.000'
def write_vtt(p,entries):p.write_text('WEBVTT\n\n'+'\n\n'.join(f'{stamp(a)} --> {stamp(b)}\n{s}' for a,b,s in entries)+'\n',encoding='utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--preview',action='store_true');p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=DURATION);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 if a.preview:
  times=[5,14,28,40,54,64,74,84,94,105,120,133,145,157,165]
  sheet=Image.new('RGB',(1280,5*390),C['bg'])
  for i,t in enumerate(times):
   frame=draw_frame(t);frame.save(a.out/f'frame-{t:03}.jpg',quality=94)
   sheet.paste(frame.resize((416,234),Image.Resampling.LANCZOS),((i%3)*426,(i//3)*390))
   dr=ImageDraw.Draw(sheet);txt(dr,((i%3)*426+8,(i//3)*390+243),f'{t}s',20,C['green'],True)
   wrap(dr,next(s for l,r,s in CAPS if l<=t<r),(i%3)*426+8,(i//3)*390+278,400,18)
  sheet.save(a.out/'contact.jpg',quality=94);draw_frame(54).save(a.out/'method-poster.jpg',quality=95)
  write_vtt(a.out/'method-chapters.vtt',PHASES);write_vtt(a.out/'method-captions.vtt',CAPS)
  print('PREVIEW',a.out);return
 dst=a.out/f'method-{a.start:03}-{a.end:03}.mp4';assert not dst.exists()
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','medium','-crf','19','-threads','3','-pix_fmt','yuv420p','-movflags','+faststart',str(dst)]
 begin=time.time()
 with (a.out/f'{dst.stem}.log').open('wb') as f:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=f)
  for i in range(a.start*FPS,a.end*FPS):
   proc.stdin.write(draw_frame(i/FPS).tobytes())
   if i%240==0:print('FRAME',i,'/',a.end*FPS,flush=True)
  proc.stdin.close();rc=proc.wait()
 assert rc==0
 receipt={'actual_exit':rc,'start':a.start,'end':a.end,'fps':FPS,'frames':(a.end-a.start)*FPS,'sha256':sha(dst),'bytes':dst.stat().st_size,'seconds':time.time()-begin,'schematic':True}
 (a.out/f'{dst.stem}.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
