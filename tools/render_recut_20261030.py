"""Re-edit existing media, retaining real playback speed and experiment scores."""
from pathlib import Path
import json, csv, hashlib, subprocess, concurrent.futures, sys
from PIL import Image, ImageDraw, ImageFont

REPO=Path('/data/xinyao/release/DriveTTO')
STAGE=REPO/'.site-staging-20261030-recut-v1'
MEDIA=REPO/'docs/assets/videos'
HUG=Path('/data/xinyao/hugsim_workspace/out/drivetto_command_v4_345_30300_20261001/full')
VIDEO=STAGE/'assets/videos'; IMAGE=STAGE/'assets/images'; EDIT=STAGE/'edit'
for p in [VIDEO,IMAGE,EDIT]:p.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
INK=(12,29,34); WHITE=(245,249,247); TEAL=(57,214,181)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(2**20),b''):h.update(c)
 return h.hexdigest()
def run(args):
 p=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-6000:])
def encode(args,dest,fps=24):
 run([*args,'-an','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-r',fps,'-threads','3','-movflags','+faststart',dest])
def text(im,xy,s,size=24,color=WHITE,bold=False):
 ImageDraw.Draw(im).text(xy,s,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=color)
def jsonsave(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def stamp(s):
 ms=round(s*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}'

review=json.loads((STAGE/'review-expanded/candidates.json').read_text())
behavior=json.loads((STAGE/'BEHAVIOR.json').read_text())['shortlist']
# Visual review excluded two candidates with distracting reconstruction artifacts.
selected=[0,1,2,3,5,6,7,8,9,10,11,12,13,14]
labels={
0:('Crossing traffic on an urban street','A truck crosses the forward view as the vehicle follows the urban route.'),
1:('An urban block with parked vehicles','The front view passes curbside parking and nearby cross traffic.'),
2:('A tree-lined residential bend','The route approaches a rightward bend between houses and roadside trees.'),
3:('Following a winding neighborhood road','A dark vehicle is visible ahead as the road curves through a residential block.'),
5:('City blocks and marked crossings','The route continues past city buildings and marked street crossings.'),
6:('A street lined with older facades','Parked vehicles and closely spaced facades frame a residential street.'),
7:('Curbside parking on both sides','A short continuous drive through a street bordered by parked vehicles.'),
8:('A suburban street under clear skies','A nearby vehicle and roadside houses appear along the forward route.'),
9:('Neighborhood traffic and lane markings','An oncoming vehicle and painted road markings are visible along the route.'),
10:('Road markings beneath roadside trees','The forward view passes painted slow-road markings and a tree-lined block.'),
11:('An open residential stretch','The route continues between low walls, homes and roadside palms.'),
12:('A palm-lined residential block','Parked cars, palms and curbside bins provide a varied neighborhood scene.'),
13:('Following traffic through a leafy block','A vehicle ahead remains visible along a road bordered by homes and trees.'),
14:('A curved road beside greenery','The route follows a gentle curve past greenery and a side street.'),
}
names={'nuscenes':'nuScenes','waymo':'Waymo','pandaset':'PandaSet'}
def gallery(i):
 r=review[i];b=behavior[i];src=Path(r['output'])/'video.mp4'
 duration=float(r['probe']['format']['duration']);assert duration==int(r['frames'])/4
 assert b['nc_bad']==[] and int(r['stop_frames'])==0
 ident=f"hugsim-{r['dataset']}-{r['scene']}-{r['mode']}-recut"
 dest=VIDEO/f'{ident}.mp4';poster=IMAGE/f'{ident}.jpg'
 encode(['-i',src,'-vf','scale=1600:600:flags=lanczos'],dest,fps=4)
 run(['-ss',duration*.35,'-i',src,'-frames:v',1,'-vf','crop=800:450:800:0','-q:v',2,'-threads',1,poster])
 title,description=labels[i]
 item={'id':ident,'dataset':names[r['dataset']],'scene':r['scene'],'difficulty':r['difficulty'],'mode':r['mode'],
 'rc':float(r['rc'])*100,'hd':float(r['hdscore'])*100,'pdms':float(r['pdms'])*100,'frames':int(r['frames']),
 'duration':duration,'src':f'assets/videos/{dest.name}','poster':f'assets/images/{poster.name}',
 'title':title,'description':description+' Complete six-camera rollout at original speed; scores refer to the complete episode.',
 'source_sha256':sha(src),'web_sha256':sha(dest),'web_bytes':dest.stat().st_size,'poster_sha256':sha(poster),
 'source_path':str(src),'source_fps':4,'review_id':i,'stop_frames':int(r['stop_frames']),'low_frames':int(r['low_frames']),
 'nc_all_recorded_details_one':True,'playback_speed':1.0}
 print('GALLERY',i,dest.name,flush=True);return item
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:items=list(ex.map(gallery,selected))
jsonsave(STAGE/'GALLERY.json',items)

timeline=[]
def append(title,path,duration,**extra):timeline.append(dict(title=title,path=str(path),duration=duration,**extra))
def clip(title,name,source,start,duration):
 dst=EDIT/f'{name}.mp4';encode(['-ss',start,'-i',source,'-t',duration,'-vf','scale=1280:720,setsar=1,fps=24'],dst)
 append(title,dst,duration,source=str(source),source_sha256=sha(source),source_start=start)
def card(title,name,im,duration):
 p=EDIT/f'{name}.png';im.save(p);dst=EDIT/f'{name}.mp4'
 encode(['-loop',1,'-i',p,'-t',duration,'-vf',f'fade=t=in:st=0:d=0.2,fade=t=out:st={duration-.2}:d=0.2'],dst)
 append(title,dst,duration)

clip('DriveTTO', 'logo',MEDIA/'drivetto-logo-opening.mp4',0,5)
im=Image.new('RGB',(1280,720),INK)
text(im,(65,95),'FROZEN MODELS. MORE SEARCH AT TEST TIME.',19,TEAL,True)
text(im,(65,200),'DriveTTO',76,bold=True)
text(im,(65,318),'Understanding Search and Selection',41,bold=True)
text(im,(65,377),'in Test-Time Trajectory Optimization',39)
text(im,(65,570),'Propose trajectories. Refine the plan. Compare before replacing.',25)
card('Search and selection at test time','opening',im,4)
im=Image.new('RGB',(1280,720),WHITE)
text(im,(45,30),'THE DRIVETTO PIPELINE',24,INK,True)
pic=Image.open(REPO/'assets/overview.png').convert('RGB');pic.thumbnail((1190,535),Image.Resampling.LANCZOS)
im.paste(pic,((1280-pic.width)//2,105+(535-pic.height)//2))
text(im,(45,665),'Endpoint search  /  Local refinement  /  Temporal fusion  /  Selection',23,INK)
card('A continuous search-and-selection pipeline','overview',im,4)
cartoon=MEDIA/'drivetto-algorithm-animation.mp4'
for name,start,title in [('endpoint',18,'1. Endpoint feedback from complete trajectories'),('refinement',27,'2. Refine around the current reference'),('fusion',45,'3. Fuse branches along the future horizon'),('selection',54,'4. Compare relative gains and keep a fallback')]:
 clip(title,name,cartoon,start,7)
for token,title in [('00c489998dd4555c','NAVSIM | Urban bend'),('0114734fd69b598e','NAVSIM | Narrow street'),('013ec5b715635a66','NAVSIM | Junction'),('003ead1914c051d7','NAVSIM | Bridge curve')]:
 clip(title,'navsim-'+token,MEDIA/f'navsim-{token}.mp4',0,6)

# Keep both short episodes complete; use meaningful motion windows from two longer ones.
windows=[(0,0,8.25),(1,0,8.5),(2,7.5,8.5),(14,2,7.5)]
clips=[]
for seq,(i,start,duration) in enumerate(windows):
 r=review[i];src=Path(r['output'])/'video.mp4';assert start+duration<=float(r['probe']['format']['duration'])
 im=Image.new('RGBA',(1280,720),(0,0,0,0));d=ImageDraw.Draw(im)
 d.rectangle((0,0,1280,91),fill=(*INK,238));d.rectangle((0,626,1280,720),fill=(*INK,235))
 text(im,(35,17),'HUGSIM  /  CLOSED-LOOP DRIVING',16,TEAL,True)
 text(im,(35,48),labels[i][0],26,bold=True)
 text(im,(835,20),names[r['dataset']]+'  /  '+r['difficulty'].upper(),20,bold=True)
 text(im,(835,53),f"RC {float(r['rc'])*100:.1f}     HD {float(r['hdscore'])*100:.1f}",23,TEAL,True)
 text(im,(35,644),r['scene']+'  /  '+r['mode'],20,bold=True)
 text(im,(35,681),'Original playback speed  |  Scores from the complete episode',18)
 text(im,(1160,656),f'{seq+1:02d}/04',22,bold=True)
 overlay=EDIT/f'hugsim-{seq}.png';im.save(overlay);dest=EDIT/f'hugsim-{seq}.mp4'
 encode(['-ss',start,'-i',src,'-loop',1,'-i',overlay,'-filter_complex',
 '[0:v]crop=800:450:800:0,scale=1280:720,setsar=1,fps=24[b];[b][1:v]overlay=0:0:format=auto',
 '-t',duration],dest)
 entry=dict(source=str(src),source_sha256=sha(src),source_start=start,source_duration=float(r['probe']['format']['duration']),
 playback_speed=1.0,view='Front-center crop, x800 y0 width800 height450',review_id=i,rc=float(r['rc'])*100,hd=float(r['hdscore'])*100)
 append('HUGSIM | '+labels[i][0],dest,duration,**entry);clips.append(entry)

im=Image.new('RGB',(1280,720),INK);d=ImageDraw.Draw(im)
text(im,(45,45),'EVALUATION ACROSS TWO BENCHMARKS',19,TEAL,True)
text(im,(45,105),'From trajectory scoring to closed-loop driving.',36,bold=True)
for j,(name,metric,value) in enumerate([('NAVTEST','PDMS','95.5'),('NAVTEST','EPDMS','92.3'),('NAVHARD','EPDMS','57.1'),('HUGSIM','RC','54.5'),('HUGSIM','HD-SCORE','40.1')]):
 x=45+j*240;d.rounded_rectangle((x,235,x+222,450),12,fill=(26,54,57))
 text(im,(x+20,263),name,17,TEAL,True);text(im,(x+15,310),value,57,bold=True);text(im,(x+20,399),metric,21)
text(im,(45,510),'Six base planners. Native / ToAD / DriveTTO-S comparisons.',27,bold=True)
text(im,(45,562),'ZTRS    GTRS    Hydra-MDP    iPad    RAP-DINO    DrivoR',24)
text(im,(45,638),'Paper-reported aggregate results; benchmark-specific configurations.',19,(184,202,198))
text(im,(45,675),'Full tables and protocols on the project page.',19,(184,202,198))
card('Five aggregate benchmark metrics','results',im,8)
im=Image.new('RGB',(1280,720),INK)
text(im,(410,200),'DriveTTO',78,bold=True);text(im,(258,344),'Explore the method and more driving examples.',29)
text(im,(323,432),'rtwotwo.github.io/DriveTTO',35,TEAL,True)
card('Explore the project','outro',im,4)

concat=EDIT/'concat.txt';concat.write_text(''.join("file '"+x['path']+"'\n" for x in timeline))
silent=EDIT/'silent.mp4'
encode(['-f','concat','-safe',0,'-i',concat],silent)
duration=sum(x['duration'] for x in timeline)
wav=EDIT/'original-score.wav'
subprocess.run([sys.executable,str(REPO/'tools/generate_recut_music.py'),'--seconds',str(duration),'--output',str(wav),'--metadata',str(EDIT/'music.json')],check=True)
dest=VIDEO/'drivetto-introduction-recut-20261030.mp4'
run(['-i',silent,'-i',wav,'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-20:TP=-2:LRA=8','-ar',48000,'-c:a','aac','-b:a','192k','-t',duration,'-movflags','+faststart',dest])
poster=IMAGE/'intro-recut-20261030.jpg'
run(['-ss',3.7,'-i',dest,'-frames:v',1,'-q:v',2,'-threads',1,poster])
teaser=IMAGE/'intro-recut-20261030.gif'
run(['-i',dest,'-t',5,'-filter_complex','fps=10,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop',0,'-threads',2,teaser])
chapters=[];vtt=['WEBVTT',''];clock=0
for x in timeline:
 c={**x,'start':clock,'end':clock+x['duration'],'rendered_sha256':sha(x['path'])};chapters.append(c)
 vtt.extend([f"{stamp(c['start'])} --> {stamp(c['end'])}",c['title'],'']);clock=c['end']
chaptersfile=VIDEO/'drivetto-introduction-recut-20261030.vtt';chaptersfile.write_text('\n'.join(vtt),encoding='utf-8')
intro=dict(duration_seconds=duration,width=1280,height=720,fps=24,src='assets/videos/'+dest.name,poster='assets/images/'+poster.name,
 chapters_src='assets/videos/'+chaptersfile.name,sha256=sha(dest),poster_sha256=sha(poster),chapters_sha256=sha(chaptersfile),
 teaser='assets/images/'+teaser.name,teaser_sha256=sha(teaser),bytes=dest.stat().st_size,chapters=chapters,
 title='DriveTTO | Search, planning and closed-loop driving',
 selection='Four selected complete-episode motion windows, 14 complete gallery rollouts, four NAVSIM saved-plan animations, and an original schematic method animation.',
 note='Recorded driving retains original playback speed; displayed RC/HD scores describe complete episodes. Main-video views crop the front camera; gallery videos retain all six views. No inference was run or result changed. Schematic method animation is not a measured trajectory. Selected examples are illustrative.',
 music=json.loads((EDIT/'music.json').read_text()),source_results_sha256=sha(HUG/'full_results.csv'))
jsonsave(STAGE/'INTRO.json',intro)
# Review one frame per chapter, including every newly selected driving window.
sheet=Image.new('RGB',(1280,((len(chapters)+2)//3)*275),INK)
for i,c in enumerate(chapters):
 p=EDIT/f'qa-{i:02d}.jpg';run(['-ss',(c['start']+c['end'])/2,'-i',dest,'-frames:v',1,'-vf','scale=426:240','-threads',1,p])
 x=(i%3)*426;y=(i//3)*275;sheet.paste(Image.open(p),(x,y));text(sheet,(x+6,y+244),f"{i+1:02d}  {c['start']:g}-{c['end']:g}s",16)
sheet.save(STAGE/'FINAL_CONTACT.jpg',quality=92)
print(json.dumps({'duration':duration,'gallery':len(items),'intro_bytes':dest.stat().st_size,'sha256':sha(dest)}),flush=True)
