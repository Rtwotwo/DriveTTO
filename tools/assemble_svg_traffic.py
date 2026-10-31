"""Assemble corrected SVG traffic and the user-selected public soundtrack."""
from pathlib import Path
import hashlib, json, subprocess
R=Path('/data/xinyao/release/DriveTTO'); S=R/'.method-svg-traffic-20261031-v1'
P=R/'.method-planners-20261031-v2'
OLD=R/'docs/assets/videos/drivetto-introduction-svg-20261031.mp4'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):
 p=subprocess.run(['ffmpeg','-nostdin','-y','-hide_banner','-loglevel','error',*map(str,args)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-5000:])
def concat(paths,out):
 f=S/(out.stem+'.txt');f.write_text(''.join("file '"+str(p)+"'\n" for p in paths))
 run(['-f','concat','-safe','0','-i',f,'-an','-c:v','copy','-map_metadata','-1','-movflags','+faststart',out])
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
def stamp(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02}.{ms:03}'
def vtt(rows):return ('WEBVTT\n\n'+''.join(f'{stamp(a)} --> {stamp(b)}\n{c}\n\n' for a,b,c in rows)).rstrip()+'\n'
assert not (S/'ASSEMBLY.json').exists()
assert sha(OLD)=='3c64d112dcd60cdbde9392278e532ae95c3d4de5db5679a0be8ac54fcf0f0bfc'
source=R/'docs/assets/animation/method-svg-traffic-20261031.js'; source_sha=sha(source)
assert not any(n in source.read_text().lower() for n in ['chainflow','drivor'])
waits=[]
for a,b in [(0,56),(56,112),(112,168)]:
 w=json.loads((S/f'method-{a:03}-{b:03}.mp4.exit.json').read_text())
 assert w['code']==0 and w['source_sha256']==source_sha and w['frames']==(b-a)*24
 waits.append(w)
method=S/'drivetto-method-traffic-20261031.mp4'
concat([S/f'method-{a:03}-{b:03}.mp4' for a,b in [(0,56),(56,112),(112,168)]],method)
# Use the soundtrack from the user's own linked DriveTTO edit. Extend an internal
# passage, crossfade both joins, and keep the original beginning/end at normal speed.
reference=S/'reference-xhs.mp4'
assert float(probe(reference)['format']['duration'])>316
music=S/'reference-soundtrack-396.m4a'
filters='[0:a]asplit=3[a][b][c];[a]atrim=0:180,asetpts=PTS-STARTPTS[a0];[b]atrim=100:184,asetpts=PTS-STARTPTS[b0];[c]atrim=180:316,asetpts=PTS-STARTPTS[c0];[a0][b0]acrossfade=d=2:c1=tri:c2=tri[ab];[ab][c0]acrossfade=d=2:c1=tri:c2=tri,afade=t=in:d=1.5,afade=t=out:st=392:d=4,loudnorm=I=-21:TP=-2:LRA=8[aout]'
run(['-i',reference,'-filter_complex',filters,'-map','[aout]','-ar','48000','-ac','2','-c:a','aac','-b:a','160k','-t','396','-map_metadata','-1',music])
assert abs(float(probe(music)['format']['duration'])-396)<.1
public=S/'drivetto-introduction-traffic-20261031.mp4'; review=S/'DriveTTO_Introduction_Anonymous.mp4'
fixed=[]
source_review=S/'previous-anonymous.mp4'
assert sha(source_review)=='72af263a09c3fb314c7b81de1e723fe6ea508425af9468588d479716f51f4781'
# Previous transient edit folders have been removed. Recover the same intervals
# from the published masters rather than depending on those scratch paths.
for name,start,duration,source_master in [('prefix',0,15,OLD),('real-scenes',183,197,OLD),('results',380,12,OLD),('outro-public',392,4,OLD),('outro-review',392,4,source_review)]:
 dst=S/(name+'.mp4')
 run(['-ss',start,'-i',source_master,'-t',duration,'-an','-c:v','libx264','-preset','fast','-crf','18','-r','24','-pix_fmt','yuv420p','-threads','6','-map_metadata','-1',dst])
 if name in ['prefix','real-scenes','results']:fixed.append(dst)
for suffix,out in [('public',public),('review',review)]:
 silent=S/f'{suffix}-silent.mp4'
 concat([fixed[0],method,fixed[1],fixed[2],S/f'outro-{suffix}.mp4'],silent)
 # Submission keeps the previously checked piano track; the public edit uses
 # the user's linked soundtrack, whose track/performer identity is unspecified.
 audio=music if suffix=='public' else OLD
 run(['-i',silent,'-i',audio,'-map','0:v','-map','1:a','-c','copy','-t','396','-map_metadata','-1','-movflags','+faststart',out])
checks=[]
for p,duration in [(method,168),(public,396),(review,396)]:
 meta=probe(p);assert abs(float(meta['format']['duration'])-duration)<.06
 v=next(s for s in meta['streams'] if s['codec_type']=='video');assert (v['width'],v['height'])==(1280,720)
 run(['-xerror','-i',p,'-f','null','-'])
 checks.append({'name':p.name,'duration':meta['format']['duration'],'decode_exit':0,'streams':meta['streams']})
 print('FULL_DECODE_OK',p.name,flush=True)
run(['-ss','138','-i',method,'-frames:v','1','-q:v','2',S/'method-poster.jpg'])
run(['-i',method,'-filter_complex','[0:v]split=3[a][b][c];[a]trim=12:15,setpts=PTS-STARTPTS[a0];[b]trim=72:75,setpts=PTS-STARTPTS[b0];[c]trim=151:154,setpts=PTS-STARTPTS[c0];[a0][b0][c0]concat=n=3:v=1:a=0,fps=8,scale=640:-1,split[p][q];[p]palettegen=stats_mode=diff[pal];[q][pal]paletteuse=dither=bayer','-loop','0',S/'method-teaser.gif'])
timeline=json.loads((S/'timeline.json').read_text());intro=json.loads((R/'docs/assets/data/intro-edit.json').read_text())
chapters=[c for c in intro['chapters'] if c['end']<=15]
chapters += [dict(title='Method | '+title,start=a+15,end=b+15,duration=b-a) for a,b,title in timeline['phases']]
chapters += [c for c in intro['chapters'] if c['start']>=183]
(S/'intro-chapters.vtt').write_text(vtt([(c['start'],c['end'],c['title']) for c in chapters]))
(S/'method-chapters.vtt').write_text(vtt(timeline['phases']))
(S/'method-captions.vtt').write_text(vtt(timeline['captions']))
for p,t in [(public,29),(public,153),(public,172),(public,386),(review,394)]:run(['-ss',t,'-i',p,'-frames:v','1','-q:v','2',S/f'{p.stem}-{t}.jpg'])
def entry(p,d):return dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size,duration=d)
r=dict(public=entry(public,396),review=entry(review,396),method=entry(method,168),old_intro_sha256=sha(OLD),complete_decode_exit_codes=[0,0,0],render_waits=waits,source_sha256=source_sha,source='docs/assets/animation/method-svg-traffic-20261031.js',render_format='SVG rendered by Sharp/librsvg, encoded by ffmpeg',labels=['Planner 1','Planner 2'],traffic='Same-direction lead vehicle follows the road tangent; ego follows with positive gap; parked vehicle remains at curb. No perpendicular crossing vehicle.',method_stage_order_unchanged=True,real_scene_intervals_unchanged=[[183,380]],metric_values_unchanged=True,public_audio={'source':'User-provided DriveTTO video','reference_url':'https://xhslink.cn/o/7L9MCxT53xS','reference_sha256':sha(reference),'music_identity':'Not specified by source','edit_segments_seconds':[[0,180],[100,184],[180,316]],'crossfade_seconds':2,'target_lufs':-21,'sha256':sha(music)},review_audio='Previously checked original piano AAC copied unchanged',schematic=True,chapters=chapters,preserved_sections=[{'name':p.name,'sha256':sha(p)} for p in fixed],checks=checks)
(S/'ASSEMBLY.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['public','review','method']}),flush=True)
