"""Update the continuous schematic's labels and street actors; retain real clips."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,shutil,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
R=Path('/data/xinyao/release/DriveTTO')
S=R/'.method-planners-20261031-v2'
PREV=R/'.method-continuous-20261031-v1'
OLD=R/'docs/assets/videos/drivetto-introduction-continuous-20261031.mp4'
ANON=PREV/'DriveTTO_Introduction_Anonymous.mp4'
S.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):
 p=subprocess.run(['ffmpeg','-nostdin','-y','-hide_banner','-loglevel','error',*map(str,args)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
def enc(src,start,duration,out):
 run(['-ss',start,'-i',src,'-t',duration,'-an','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-r','24','-threads','3','-movflags','+faststart',out])
def concat(paths,out):
 p=S/(out.stem+'.txt');p.write_text(''.join("file '"+str(x)+"'\n" for x in paths))
 run(['-f','concat','-safe','0','-i',p,'-an','-c:v','copy','-movflags','+faststart',out])
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
assert sha(OLD)=='e665edc02efe7af8ac947fd1de5b38d8f82b47766b336468be2a6f7cd6afa197'
assert sha(ANON)=='46c519ab172dcd32545db809ba3e955c211601a5871d471ba1d274516d6be7ae'
source=(R/'tools/render_continuous_method.py').read_text()
assert not any(s in source.lower() for s in ['chainflow','drivor'])
subprocess.run([sys.executable,str(R/'tools/render_continuous_method.py'),'--out',str(S),'--preview'],check=True)
def render(q):
 a,b=q
 p=subprocess.run([sys.executable,str(R/'tools/render_continuous_method.py'),'--out',str(S),'--start',str(a),'--end',str(b)])
 assert p.returncode==0
 return {'start':a,'end':b,'actual_exit':p.returncode}
with ThreadPoolExecutor(max_workers=3) as ex:waits=list(ex.map(render,[(0,58),(58,116),(116,168)]))
(S/'RENDER_WAITS.json').write_text(json.dumps(waits,indent=2))
method=S/'drivetto-method-two-planners-20261031.mp4'
concat([S/f'method-{a:03}-{b:03}.mp4' for a,b in [(0,58),(58,116),(116,168)]],method)
# Preserve score card values. Replace only the base-planner names, not any metric.
run(['-ss','386','-i',OLD,'-frames:v','1',S/'results-before.png'])
im=Image.open(S/'results-before.png').convert('RGB');d=ImageDraw.Draw(im)
d.rectangle((40,548,1240,610),fill=(12,29,34))
label='Six-planner transfer with the single-scorer variant, DriveTTO-S.'
d.text((45,562),label,font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24),fill=(245,249,247))
im.save(S/'results.png')
run(['-loop','1','-i',S/'results.png','-t','12','-vf','fade=t=in:st=0:d=0.2,fade=t=out:st=11.8:d=0.2','-an','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-r','24','-threads','3',S/'results.mp4'])
jobs=[(OLD,183,197,S/'real-scenes.mp4'),(OLD,392,4,S/'outro-public.mp4'),(ANON,392,4,S/'outro-review.mp4')]
with ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(lambda q:enc(*q),jobs))
print('REAL_SCENE_AND_OUTRO_EXTRACTS_COMPLETE',flush=True)
public=S/'drivetto-introduction-two-planners-20261031.mp4';review=S/'DriveTTO_Introduction_Anonymous.mp4'
for suffix,out in [('public',public),('review',review)]:
 silent=S/f'{suffix}-silent.mp4'
 concat([PREV/'prefix.mp4',method,S/'real-scenes.mp4',S/'results.mp4',S/f'outro-{suffix}.mp4'],silent)
 # Copy the existing piano AAC without changing performance, level or timing.
 run(['-i',silent,'-i',OLD,'-map','0:v','-map','1:a','-c','copy','-t','396','-map_metadata','-1','-movflags','+faststart',out])
for p,duration in [(method,168),(public,396),(review,396)]:
 meta=probe(p);assert abs(float(meta['format']['duration'])-duration)<.06
 run(['-xerror','-i',p,'-f','null','-'])
 print('FULL_DECODE_OK',p.name,flush=True)
run(['-i',method,'-filter_complex','[0:v]split=3[a][b][c];[a]trim=34:37,setpts=PTS-STARTPTS[a0];[b]trim=72:75,setpts=PTS-STARTPTS[b0];[c]trim=120:123,setpts=PTS-STARTPTS[c0];[a0][b0][c0]concat=n=3:v=1:a=0,fps=8,scale=640:-1,split[p][q];[p]palettegen=stats_mode=diff[pal];[q][pal]paletteuse=dither=bayer','-loop','0',S/'method-teaser.gif'])
shutil.copy2(PREV/'intro-chapters.vtt',S/'intro-chapters.vtt')
for p,t in [(public,90),(public,386),(review,394)]:run(['-ss',t,'-i',p,'-frames:v','1','-q:v','2',S/f'{p.stem}-{t}.jpg'])
def entry(p,d):return dict(name=p.name,sha256=sha(p),bytes=p.stat().st_size,duration=d)
r={'public':entry(public,396),'review':entry(review,396),'method':entry(method,168),'old_intro_sha256':sha(OLD),'old_review_sha256':sha(ANON),'complete_decode_exit_codes':[0,0,0],'render_waits':waits,'source_sha256':sha(R/'tools/render_continuous_method.py'),'labels':['Planner 1','Planner 2'],'actor_art':'Original vector sedan silhouettes with windows, lights, wheels and mirrors; pedestrians and cones on roadside','method_geometry_and_timing_unchanged':True,'real_scene_intervals_unchanged':[[183,380]],'metric_values_unchanged':True,'audio':'Existing piano AAC copied unchanged','schematic':True}
(S/'ASSEMBLY.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
