"""Re-cut the five-minute introduction around eight hard/extreme rollouts."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import csv,json,hashlib,subprocess
from PIL import Image,ImageDraw,ImageFont

R=Path('/data/xinyao/release/DriveTTO')
S=R/'.site-staging-20261030-piano-v1';E=S/'edit';E.mkdir(exist_ok=True)
OLD=R/'.site-staging-20261030-recut-v1'
names={'pandaset':'PandaSet','nuscenes':'nuScenes','waymo':'Waymo'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def run(args):
 p=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
def enc(args,dest,fps=24):run([*args,'-an','-c:v','libx264','-preset','medium','-crf',20,'-r',fps,'-pix_fmt','yuv420p','-threads',3,'-movflags','+faststart',dest])
def text(im,xy,s,size=22,color=(245,249,247),bold=False):
 ImageDraw.Draw(im).text(xy,s,font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size),fill=color)
def stamp(s):
 n=round(s*1000);return f'{n//3600000:02d}:{n//60000%60:02d}:{n//1000%60:02d}.{n%1000:03d}'

selected=json.loads((S/'SELECTED.json').read_text())
assert len(selected)==10 and sum(x['difficulty']=='easy' for x in selected)==2
assert sum(x['duration'] for x in selected)==173
old=json.loads((R/'docs/assets/data/intro-edit.json').read_text())
existing={x['id']:x for x in json.loads((R/'docs/assets/data/media-selection.json').read_text())['videos']}
rows=list(csv.DictReader(Path('/data/xinyao/hugsim_workspace/out/drivetto_command_v4_345_30300_20261001/full/full_results.csv').open()))

def render_episode(pair):
 i,x=pair;src=Path(x['source']);assert sha(src)==x['source_sha256']
 row=next(r for r in rows if (r['dataset'],r['scene'],r['mode'])==(x['dataset'],x['scene'],x['mode']))
 assert abs(float(row['rc'])*100-x['rc'])<1e-8 and abs(float(row['hdscore'])*100-x['hd'])<1e-8
 assert x['rc']==100 and x['hd']>=94 and x['nc']==1
 im=Image.new('RGBA',(1280,720),(0,0,0,0));d=ImageDraw.Draw(im)
 d.rectangle((0,0,1280,91),fill=(12,29,34,238));d.rectangle((0,626,1280,720),fill=(12,29,34,235))
 group='ROAD GEOMETRY' if i<3 else ('URBAN TURNS' if i<6 else 'TRAFFIC INTERACTIONS')
 text(im,(35,17),'HUGSIM  /  '+group,16,(57,214,181),True)
 text(im,(35,48),x['title'],25,bold=True)
 text(im,(880,20),names[x['dataset']]+'  /  '+x['difficulty'].upper(),20,bold=True)
 text(im,(880,53),f"RC {x['rc']:.1f}   HD {x['hd']:.1f}",22,(57,214,181),True)
 text(im,(35,644),x['scene']+'  /  '+x['mode'],20,bold=True)
 text(im,(35,681),'Complete episode at original speed  |  Full-episode scores',18)
 text(im,(1160,656),f'{i+1:02d}/10',22,bold=True)
 overlay=E/f'overlay-{i:02d}.png';im.save(overlay);p=E/f'episode-{i:02d}.mp4'
 enc(['-i',src,'-loop',1,'-i',overlay,'-filter_complex','[0:v]crop=800:450:800:0,scale=1280:720,setsar=1,fps=24[b];[b][1:v]overlay=0:0:format=auto','-t',x['duration']],p)
 chapter=dict(title='HUGSIM | '+x['title'],path=str(p),duration=x['duration'],source=str(src),source_sha256=x['source_sha256'],source_start=0,source_duration=x['duration'],playback_speed=1.0,view='Front-center crop, x800 y0 width800 height450',rc=x['rc'],hd=x['hd'],difficulty=x['difficulty'],complete_episode=True)
 if x['existing_id'] in existing:
  item=dict(existing[x['existing_id']]);item.update(title=x['title'],description=x['context']+' Complete six-camera rollout at original speed; scores refer to the complete episode.')
 else:
  ident=f"hugsim-{x['dataset']}-{x['scene']}-{x['mode']}-piano"
  video=R/'docs/assets/videos'/f'{ident}.mp4';poster=R/'docs/assets/images'/f'{ident}.jpg'
  assert not video.exists() and not poster.exists()
  enc(['-i',src,'-vf','scale=1600:600:flags=lanczos'],video,4)
  run(['-ss',x['duration']*.35,'-i',src,'-frames:v',1,'-vf','crop=800:450:800:0','-q:v',2,'-threads',1,poster])
  item=dict(id=ident,dataset=names[x['dataset']],scene=x['scene'],difficulty=x['difficulty'],mode=x['mode'],rc=x['rc'],hd=x['hd'],pdms=float(row['pdms'])*100,frames=int(row['frames']),duration=x['duration'],src='assets/videos/'+video.name,poster='assets/images/'+poster.name,title=x['title'],description=x['context']+' Complete six-camera rollout at original speed; scores refer to the complete episode.',source_sha256=x['source_sha256'],web_sha256=sha(video),web_bytes=video.stat().st_size,poster_sha256=sha(poster),source_path=str(src),source_fps=4,stop_frames=int(row['stop_frames']),low_frames=int(row['low_frames']),nc_all_recorded_details_one=True,playback_speed=1.0)
 print('RENDERED',i+1,x['title'],flush=True)
 return chapter,item

with ThreadPoolExecutor(max_workers=3) as ex:pairs=list(ex.map(render_episode,enumerate(selected)))
timeline=[]
for c in old['chapters']:
 if c['title'].startswith('HUGSIM |'):continue
 if c['title']=='Five aggregate benchmark metrics':break
 x=dict(c)
 if c['title']=='A continuous search-and-selection pipeline':
  p=E/'overview.mp4';enc(['-loop',1,'-i',OLD/'edit/overview.png','-t',6],p);x.update(path=str(p),duration=6)
 timeline.append(x)
timeline.extend(p[0] for p in pairs)
timeline.extend(dict(x) for x in old['chapters'][-2:])
assert sum(x['duration'] for x in timeline)==300
clock=0;vtt=['WEBVTT','']
for c in timeline:
 c.update(start=clock,end=clock+c['duration'],rendered_sha256=sha(c['path']));clock=c['end']
 vtt.extend([f"{stamp(c['start'])} --> {stamp(c['end'])}",c['title'],''])
listing=E/'concat.txt';listing.write_text(''.join("file '"+c['path']+"'\n" for c in timeline))
run(['-f','concat','-safe',0,'-i',listing,'-an','-c','copy','-movflags','+faststart',E/'silent.mp4'])
chapters=R/'docs/assets/videos/drivetto-introduction-piano-20261030.vtt';chapters.write_text('\n'.join(vtt))
intro={**old,'chapters':timeline,'chapters_src':'assets/videos/'+chapters.name,'chapters_sha256':sha(chapters),'selection':'A five-minute introduction to DriveTTO: the complete algorithm animation, four NAVSIM plans at PDMS 100, and ten complete HUGSIM episodes with RC 100 and HD-Score 94.2–100. Seven hard and one extreme scene follow two easy introductions. Relaxed acoustic piano accompanies the film; all ten rollouts are available separately in the gallery.'}
save(S/'INTRO_VISUAL.json',intro);save(S/'GALLERY.json',[p[1] for p in pairs])
sheet=Image.new('RGB',(1280,((len(timeline)+2)//3)*275),(12,29,34))
for i,c in enumerate(timeline):
 p=E/f'qa-{i:02d}.jpg';run(['-ss',c['duration']/2,'-i',c['path'],'-frames:v',1,'-vf','scale=426:240','-threads',1,p])
 x=(i%3)*426;y=(i//3)*275;sheet.paste(Image.open(p),(x,y));text(sheet,(x+5,y+244),f"{i+1:02d}  {c['start']:g}-{c['end']:g}s",16)
sheet.save(S/'CONTACT.jpg',quality=92)
print('COMPLETE',len(timeline),300,flush=True)
