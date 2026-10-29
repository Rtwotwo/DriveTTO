"""Build the requested five-minute film with complete high-score episodes."""
from pathlib import Path
import json,hashlib,subprocess,sys,concurrent.futures
from PIL import Image,ImageDraw,ImageFont
R=Path('/data/xinyao/release/DriveTTO');S=R/'.site-staging-20261030-recut-v1';E=S/'five-minute';E.mkdir(exist_ok=True)
V=S/'assets/videos';I=S/'assets/images'
old=json.loads((S/'INTRO.json').read_text());review=json.loads((S/'review-expanded/candidates.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):
 p=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-5000:])
def enc(args,p):run([*args,'-an','-c:v','libx264','-preset','medium','-crf',20,'-r',24,'-pix_fmt','yuv420p','-threads',3,'-movflags','+faststart',p])
def text(im,xy,s,size=24,color=(245,249,247),bold=False):ImageDraw.Draw(im).text(xy,s,font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size),fill=color)
def stamp(s):
 n=round(s*1000);return f'{n//3600000:02d}:{n//60000%60:02d}:{n//1000%60:02d}.{n%1000:03d}'
timeline=[]
def add(c,p=None,d=None):
 x=dict(c)
 for k in ('start','end','rendered_sha256'):x.pop(k,None)
 if p is not None:x['path']=str(p)
 if d is not None:x['duration']=d
 timeline.append(x)
add(old['chapters'][0]);add(old['chapters'][1])
p=E/'overview.mp4';enc(['-loop',1,'-i',S/'edit/overview.png','-t',8.75],p);add(old['chapters'][2],p,8.75)
method_titles=['Search. Compare. Select.','A bank of complete trajectories','Learn from where the path ends','Refine within a bounded neighborhood','Compare against the same reference','Fuse along the same horizon','Select conservatively; keep a fallback','A new path. The same frozen models.']
source=R/'docs/assets/videos/drivetto-algorithm-animation.mp4'
for i,title in enumerate(method_titles):
 p=E/f'method-{i}.mp4'
 enc(['-ss',i*9,'-i',source,'-t',9],p)
 add(dict(title='Method | '+title,path=str(p),duration=9,source=str(source),source_start=i*9,source_sha256=sha(source)))
for c in old['chapters'][7:11]:add(c)
names={'nuscenes':'nuScenes','waymo':'Waymo','pandaset':'PandaSet'}
g={x['review_id']:x for x in json.loads((S/'GALLERY.json').read_text())}
# All thirteen episodes have RC=100 and HD>=94.0. None have recorded stop frames.
order=[0,1,5,6,7,8,9,10,12,13,2,11,14]
def episode(pair):
 seq,i=pair;r=review[i];item=g[i];src=Path(r['output'])/'video.mp4';duration=float(r['probe']['format']['duration'])
 assert item['rc']==100 and item['hd']>=94 and item['stop_frames']==0 and duration<=25
 im=Image.new('RGBA',(1280,720),(0,0,0,0));d=ImageDraw.Draw(im)
 d.rectangle((0,0,1280,91),fill=(12,29,34,238));d.rectangle((0,626,1280,720),fill=(12,29,34,235))
 group='URBAN STREETS' if seq<5 else ('RESIDENTIAL ROUTES' if seq<10 else 'ROAD GEOMETRY')
 text(im,(35,17),'HUGSIM  /  '+group,16,(57,214,181),True)
 text(im,(35,48),item['title'],26,bold=True)
 text(im,(835,20),names[r['dataset']]+'  /  '+r['difficulty'].upper(),20,bold=True)
 text(im,(835,53),f"RC {item['rc']:.1f}     HD {item['hd']:.1f}",23,(57,214,181),True)
 text(im,(35,644),r['scene']+'  /  '+r['mode'],20,bold=True)
 text(im,(35,681),'Complete episode at original speed  |  Full-episode scores',18)
 text(im,(1160,656),f'{seq+1:02d}/13',22,bold=True)
 over=E/f'overlay-{seq}.png';im.save(over);p=E/f'episode-{seq}.mp4'
 enc(['-i',src,'-loop',1,'-i',over,'-filter_complex','[0:v]crop=800:450:800:0,scale=1280:720,setsar=1,fps=24[b];[b][1:v]overlay=0:0:format=auto','-t',duration],p)
 print('EPISODE',seq+1,item['title'],duration,flush=True)
 return dict(title='HUGSIM | '+item['title'],path=str(p),duration=duration,source=str(src),source_sha256=sha(src),source_start=0,
 source_duration=duration,playback_speed=1.0,view='Front-center crop, x800 y0 width800 height450',review_id=i,rc=item['rc'],hd=item['hd'],difficulty=item['difficulty'],complete_episode=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:timeline.extend(ex.map(episode,enumerate(order)))
p=E/'results.mp4';enc(['-loop',1,'-i',S/'edit/results.png','-t',12],p);add(old['chapters'][-2],p,12)
add(old['chapters'][-1])
duration=sum(c['duration'] for c in timeline);assert duration==300
listing=E/'concat.txt';listing.write_text(''.join("file '"+c['path']+"'\n" for c in timeline))
silent=E/'silent.mp4';run(['-f','concat','-safe',0,'-i',listing,'-an','-c','copy','-movflags','+faststart',silent])
music=E/'original-score.wav'
subprocess.run([sys.executable,str(R/'tools/generate_recut_music.py'),'--seconds',str(duration),'--output',str(music),'--metadata',str(E/'music.json'),'--drive-start','89.75','--closing-start','284'],check=True)
dest=V/'drivetto-introduction-five-minute-20261030.mp4'
run(['-i',silent,'-i',music,'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-20:TP=-2:LRA=8','-ar',48000,'-c:a','aac','-b:a','192k','-t',duration,'-movflags','+faststart',dest])
chapters=[];vtt=['WEBVTT',''];clock=0
for c in timeline:
 c.update(start=clock,end=clock+c['duration'],rendered_sha256=sha(c['path']));chapters.append(c);clock=c['end']
 vtt.extend([f"{stamp(c['start'])} --> {stamp(c['end'])}",c['title'],''])
vttpath=V/'drivetto-introduction-five-minute-20261030.vtt';vttpath.write_text('\n'.join(vtt))
intro={**old,'duration_seconds':duration,'src':'assets/videos/'+dest.name,'chapters_src':'assets/videos/'+vttpath.name,
 'sha256':sha(dest),'chapters_sha256':sha(vttpath),'bytes':dest.stat().st_size,'chapters':chapters,'music':json.loads((E/'music.json').read_text()),
 'selection':'A five-minute introduction to DriveTTO: the complete algorithm animation, four NAVSIM plans at PDMS 100, and thirteen complete HUGSIM episodes with RC 100 and HD-Score 94.2–100. Original instrumental music accompanies the film; 14 complete rollouts are available in the gallery.',
 'note':'Recorded driving retains complete episodes at original playback speed. RC/HD scores describe those complete episodes. Main-video views crop the front camera; gallery videos retain all six views. Schematic method animation is not a measured trajectory. These selected high-score examples are illustrative; aggregate experiment results are unchanged.'}
(S/'INTRO_SHORT_PREVIEW.json').write_text(json.dumps(old,indent=2)+'\n')
(S/'INTRO.json').write_text(json.dumps(intro,indent=2,ensure_ascii=False)+'\n')
sheet=Image.new('RGB',(1280,((len(chapters)+2)//3)*275),(12,29,34))
for i,c in enumerate(chapters):
 p=E/f'qa-{i:02d}.jpg';run(['-ss',(c['start']+c['end'])/2,'-i',dest,'-frames:v',1,'-vf','scale=426:240','-threads',1,p])
 x=(i%3)*426;y=(i//3)*275;sheet.paste(Image.open(p),(x,y));text(sheet,(x+6,y+244),f"{i+1:02d}  {c['start']:g}-{c['end']:g}s",16)
sheet.save(S/'EXTENDED_CONTACT.jpg',quality=92)
print(json.dumps({'duration':duration,'intro_sha256':intro['sha256'],'bytes':intro['bytes'],'complete_hugsim_episodes':13}),flush=True)
