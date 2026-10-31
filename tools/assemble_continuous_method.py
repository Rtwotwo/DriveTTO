"""Replace only the old 72 s explainer; preserve selected real-scene clips."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,sys
R=Path('/data/xinyao/release/DriveTTO');S=R/'.method-continuous-20261031-v1'
OLD=R/'docs/assets/videos/drivetto-introduction-piano-20261030.mp4'
ANON=R/'.submission-staging-20261030-v1/01_DriveTTO_Introduction.mp4'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):
 p=subprocess.run(['ffmpeg','-nostdin','-y','-hide_banner','-loglevel','error',*map(str,args)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
def enc(inp,start,seconds,out):
 if '--finish-only' in sys.argv and out.exists():return str(out)
 run(['-ss',start,'-i',inp,'-t',seconds,'-an','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-r','24','-threads','3','-movflags','+faststart',out]);return str(out)
def concat(paths,out):
 if '--finish-only' in sys.argv and out.exists():return
 listing=S/(out.stem+'.txt');listing.write_text(''.join("file '"+str(p)+"'\n" for p in paths))
 run(['-f','concat','-safe','0','-i',listing,'-an','-c','copy','-movflags','+faststart',out])
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
assert sha(ANON)=='689d4180dcbc59e19962dc7473f7a14a2f44c111a48038d2d022edb09fe32968'
old=json.loads((R/'docs/assets/data/intro-edit.json').read_text());assert sha(OLD)==old['sha256']
parts=[S/f'method-{a:03}-{b:03}.mp4' for a,b in [(0,58),(58,116),(116,168)]]
for p in parts:assert sha(p)==json.loads(p.with_suffix('.json').read_text())['sha256']
method=S/'drivetto-method-continuous-20261031.mp4';concat(parts,method)
jobs=[(OLD,0,15,S/'prefix.mp4'),(OLD,87,213,S/'suffix-public.mp4'),(ANON,87,213,S/'suffix-review.mp4')]
with ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(lambda q:enc(*q),jobs))
concat([S/'prefix.mp4',method,S/'suffix-public.mp4'],S/'public-silent.mp4')
concat([S/'prefix.mp4',method,S/'suffix-review.mp4'],S/'review-silent.mp4')
# Extend the already cleared solo-piano recording by an internal musical passage.
# 120+100+180 seconds, two 2-second crossfades = 396 seconds.
if '--finish-only' not in sys.argv:run(['-i',OLD,'-filter_complex','[0:a]asplit=3[a][b][c];[a]atrim=0:120,asetpts=PTS-STARTPTS[a0];[b]atrim=20:120,asetpts=PTS-STARTPTS[b0];[c]atrim=120:300,asetpts=PTS-STARTPTS[c0];[a0][b0]acrossfade=d=2:c1=tri:c2=tri[ab];[ab][c0]acrossfade=d=2:c1=tri:c2=tri[out]','-map','[out]','-c:a','pcm_s16le',S/'piano-396.wav'])
public=S/'drivetto-introduction-continuous-20261031.mp4';review=S/'DriveTTO_Introduction_Anonymous.mp4'
for silent,out in [(S/'public-silent.mp4',public),(S/'review-silent.mp4',review)]:
 if '--finish-only' in sys.argv and out.exists():continue
 run(['-i',silent,'-i',S/'piano-396.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k','-t','396','-map_metadata','-1','-movflags','+faststart',out])
for p,seconds in [(method,168),(public,396),(review,396)]:
 x=probe(p);assert abs(float(x['format']['duration'])-seconds)<.05
 run(['-xerror','-i',p,'-f','null','-'])
 print('DECODE_OK',p.name,p.stat().st_size,flush=True)
run(['-ss','54','-i',method,'-frames:v','1','-q:v','2',S/'method-poster.jpg'])
run(['-i',method,'-filter_complex','[0:v]split=3[a][b][c];[a]trim=34:37,setpts=PTS-STARTPTS[a0];[b]trim=72:75,setpts=PTS-STARTPTS[b0];[c]trim=120:123,setpts=PTS-STARTPTS[c0];[a0][b0][c0]concat=n=3:v=1:a=0,fps=8,scale=640:-1,split[p][q];[p]palettegen=stats_mode=diff[pal];[q][pal]paletteuse=dither=bayer','-loop','0',S/'method-continuous-teaser.gif'])
def stamp(t):
 n=round(t*1000);return f'{n//3600000:02d}:{n//60000%60:02d}:{n//1000%60:02d}.{n%1000:03d}'
chapters=[]
for c in old['chapters']:
 if c['end']<=15:chapters.append({k:c[k] for k in ['title','start','end','duration']})
from render_continuous_method import PHASES,CAPS
chapters.extend(dict(title='Method | '+s,start=15+a,end=15+b,duration=b-a) for a,b,s in PHASES)
for c in old['chapters']:
 if c['start']>=87:
  q={k:c[k] for k in ['title','start','end','duration']};q['start']+=96;q['end']+=96;chapters.append(q)
assert chapters[-1]['end']==396
assert all(a['end']==b['start'] for a,b in zip(chapters,chapters[1:]))
(S/'intro-chapters.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f"{stamp(c['start'])} --> {stamp(c['end'])}\n{c['title']}" for c in chapters)+'\n')
receipt={'public':{'name':public.name,'sha256':sha(public),'bytes':public.stat().st_size,'duration':396},'review':{'name':review.name,'sha256':sha(review),'bytes':review.stat().st_size,'duration':396},'method':{'name':method.name,'sha256':sha(method),'bytes':method.stat().st_size,'duration':168},'old_intro_sha256':sha(OLD),'old_review_sha256':sha(ANON),'source_intervals_preserved':[[0,15],[87,300]],'replaced_interval':[15,87],'new_method_interval':[15,183],'chapters':chapters,'audio':'Existing relaxed piano; 2 s internal crossfades; no speech','complete_decode_exit_codes':[0,0,0],'schematic':True}
(S/'ASSEMBLY.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
