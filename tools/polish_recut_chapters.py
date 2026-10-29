"""Renumber the four extracted cartoon chapters and finalize their edit metadata."""
from pathlib import Path
import json, subprocess, hashlib
from PIL import Image, ImageDraw, ImageFont
R=Path('/data/xinyao/release/DriveTTO');S=R/'.site-staging-20261030-recut-v1';E=S/'edit'
def run(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
intro=json.loads((S/'INTRO.json').read_text());chapters=intro['chapters']
for i,c in enumerate(chapters[3:7]):
 im=Image.new('RGBA',(1280,720),(0,0,0,0));d=ImageDraw.Draw(im)
 d.rectangle((1094,15,1250,79),fill='#FFF9ED')
 d.rounded_rectangle((1110,29,1220,67),15,fill='#F2EDDE',outline='#173F42',width=2)
 d.text((1126,38),f'{i+1:02d} / 04',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',16),fill='#173F42')
 d.rectangle((40,693,1240,715),fill='#FFF9ED')
 for j in range(4):d.rounded_rectangle((50+j*300,699,330+j*300,705),3,fill='#173F42' if j<=i else '#E4E8DC')
 overlay=E/f'chapter-overlay-{i}.png';im.save(overlay)
 dest=E/f'chapter-four-{i}.mp4'
 run(['-ss',c['source_start'],'-i',c['source'],'-loop',1,'-i',overlay,'-filter_complex','[0:v][1:v]overlay=0:0:format=auto','-t',c['duration'],'-an','-c:v','libx264','-preset','medium','-crf',20,'-pix_fmt','yuv420p','-r',24,'-threads',3,'-movflags','+faststart',dest])
 c['path']=str(dest);c['rendered_sha256']=sha(dest);c['editorial_overlay']='Four-chapter numbering; underlying algorithm animation unchanged.'
listing=E/'concat-final.txt';listing.write_text(''.join("file '"+c['path']+"'\n" for c in chapters))
silent=E/'silent-final.mp4'
run(['-f','concat','-safe',0,'-i',listing,'-an','-c','copy','-movflags','+faststart',silent])
dest=S/intro['src']
run(['-i',silent,'-i',E/'original-score.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-20:TP=-2:LRA=8','-ar',48000,'-c:a','aac','-b:a','192k','-t',intro['duration_seconds'],'-movflags','+faststart',dest])
intro['sha256']=sha(dest);intro['bytes']=dest.stat().st_size
intro['selection']='From endpoint feedback and trajectory refinement to NAVSIM plans and closed-loop driving, with original instrumental music. Explore 14 complete rollouts in the gallery.'
(S/'INTRO.json').write_text(json.dumps(intro,indent=2,ensure_ascii=False)+'\n')
sheet=Image.new('RGB',(1280,((len(chapters)+2)//3)*275),(12,29,34));d=ImageDraw.Draw(sheet)
for i,c in enumerate(chapters):
 p=E/f'qa-final-{i:02d}.jpg';run(['-ss',(c['start']+c['end'])/2,'-i',dest,'-frames:v',1,'-vf','scale=426:240','-threads',1,p])
 x=(i%3)*426;y=(i//3)*275;sheet.paste(Image.open(p),(x,y));d.text((x+6,y+244),f"{i+1:02d}  {c['start']:g}-{c['end']:g}s",font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16),fill='white')
sheet.save(S/'FINAL_CONTACT.jpg',quality=92)
print(json.dumps({'sha256':intro['sha256'],'duration':intro['duration_seconds'],'bytes':intro['bytes']}))
