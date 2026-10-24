"""Render a five-second DriveTTO brand opening and prepend it without re-encoding the original.

Uses four already-public HUGSIM videos as the moving background and the project's
existing dual-trajectory favicon geometry. No experiment outputs are modified.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SECONDS, SS = 1280, 720, 24, 5, 2
CREAM = (255, 249, 237)
MINT = (180, 223, 209)
TEAL = (23, 107, 97)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ease(x):
    x = max(0., min(1., x))
    return x * x * (3 - 2 * x)

def font(size, bold=False):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans' + ('-Bold' if bold else '') + '.ttf', size * SS)

def bezier(p0, p1, p2, p3):
    pts = []
    for i in range(70):
        t = i / 69
        pts.append(tuple((1-t)**3*p0[k] + 3*(1-t)**2*t*p1[k] + 3*(1-t)*t*t*p2[k] + t**3*p3[k] for k in (0, 1)))
    return pts

CURVES = [
    bezier((15,47),(17,34),(30,40),(32,29)) + bezier((32,29),(34,18),(40,18),(49,17))[1:],
    bezier((15,47),(20,36),(37,43),(41,31)) + bezier((41,31),(45,19),(46,21),(49,17))[1:],
]

def overlay(t):
    # A dark green scrim keeps the moving footage secondary to the brand.
    image = Image.new('RGBA', (W*SS, H*SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    white = (249, 251, 247)
    title_font = font(104, True)
    drive_width = d.textlength('Drive', font=title_font) / SS
    title_width = d.textlength('DriveTTO', font=title_font) / SS
    icon_size, gap = 144, 30
    left = (W - icon_size - gap - title_width) / 2
    top = 242

    def box(coords, fill, radius=0, outline=None, width=1):
        d.rounded_rectangle(tuple(round(v*SS) for v in coords), radius=radius*SS, fill=fill, outline=outline, width=width*SS)

    def label(text, x, y, size, color, alpha=1, bold=False, center=False):
        f = font(size, bold)
        if center:
            x -= d.textlength(text, font=f) / (2*SS)
        d.text((round(x*SS), round(y*SS)), text, font=f, fill=(*color, round(255*ease(alpha))), anchor='lt')

    icon_alpha = ease((t-.10)/.45)
    if icon_alpha > 0:
        box((left,top,left+icon_size,top+icon_size), (*TEAL,round(245*icon_alpha)), 35,
            (*MINT,round(70*icon_alpha)), 1)
    for index, curve in enumerate(CURVES):
        p = ease((t - .25 - index*.22)/1.25)
        pts = [(round((left+x/64*icon_size)*SS),round((top+y/64*icon_size)*SS)) for x,y in curve]
        n = max(0, min(len(pts), int(p*len(pts))))
        color = MINT if index == 0 else white
        if n >= 2:
            d.line(pts[:n], fill=(*color,255), width=round(4/64*icon_size*SS), joint='curve')
            x,y = pts[n-1]; r = 4.2/64*icon_size*SS
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*color,255))
    if t > .25:
        for px,py,a in [(15,47,ease((t-.25)/.3)),(49,17,ease((t-1.35)/.35))]:
            x=(left+px/64*icon_size)*SS; y=(top+py/64*icon_size)*SS; r=4/64*icon_size*SS
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*white,round(255*a)))

    reveal=ease((t-.85)/.8)
    tx=left+icon_size+gap
    ty=top+23+18*(1-reveal)
    label('Drive',tx,ty,104,white,reveal,True)
    label('TTO',tx+drive_width,ty,104,MINT,reveal,True)
    subtitle=ease((t-1.55)/.65)
    label('Understanding Search and Selection',W/2,426+8*(1-subtitle),27,white,subtitle,center=True)
    label('in Test-Time Trajectory Optimization',W/2,466+8*(1-subtitle),27,white,subtitle,center=True)
    label('NAVSIM  /  HUGSIM',W/2,606,16,MINT,ease((t-1.9)/.65),center=True)
    # Two short rules frame the restrained project label.
    a=round(115*ease((t-1.9)/.65))
    for xa,xb in [(410,506),(774,870)]:
        d.line((xa*SS,616*SS,xb*SS,616*SS),fill=(*MINT,a),width=SS)
    image = Image.alpha_composite(Image.new('RGBA', image.size, (6, 23, 27, 158)), image)
    # Arrive at exactly the old cartoon's cream background before the splice.
    fade=ease((t-4.42)/.54)
    if fade:
        image=Image.alpha_composite(image,Image.new('RGBA',image.size,(*CREAM,round(255*fade))))
    return image.resize((W,H),Image.Resampling.LANCZOS)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    root=Path(args.root); out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    ff='/usr/bin/ffmpeg'
    def run(*args):
        subprocess.run([ff,'-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)
    def info(p):
        return json.loads(subprocess.check_output(['/usr/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
    source=root/'docs/assets/videos/drivetto-introduction.mp4'
    assert sha(source)=='f1a72131b0845b684d6941e667fe64275c8dbae0b6b63c984ff24fcb1d6d94e4'
    clips=[
        'nuscenes-scene-0166-hard_00', 'waymo-166085257829_0_200-hard_00',
        'nuscenes-scene-0167-extreme_01', 'waymo-322492347634_0_200-extreme_01',
    ]
    inputs=[];filters=[];provenance=[]
    for i,name in enumerate(clips):
        p=root/'docs/assets/videos'/f'{name}.mp4'
        inputs+=['-ss','0.5','-i',str(p)]
        filters.append(f'[{i}:v]crop=iw/3:ih/2:iw/3:0,scale=640:360:flags=lanczos,fps=24,setpts=PTS-STARTPTS[v{i}]')
        provenance.append({'path':str(p.relative_to(root)),'sha256':sha(p),'trim_start_seconds':.5,'duration_seconds':5,'view':'front-center camera'})
    filters.append('[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|640_0|0_360|640_360,fade=t=in:st=0:d=0.3[b]')
    run(*inputs,'-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map','[b]','-t',SECONDS,'-an','-c:v','libx264','-crf','19','-preset','fast','-threads','4','-pix_fmt','yuv420p',out/'background.mp4')
    print('Moving background rendered',flush=True)
    logo=out/'drivetto-logo-opening.mp4'
    cmd=[ff,'-hide_banner','-loglevel','error','-y','-i',str(out/'background.mp4'),'-f','rawvideo','-pixel_format','rgba','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-filter_complex_threads','2','-filter_complex','[0:v][1:v]overlay=0:0:shortest=1[v]','-map','[v]','-frames:v',str(SECONDS*FPS),'-an','-c:v','libx264','-preset','fast','-crf','18','-threads','4','-pix_fmt','yuv420p','-video_track_timescale','12288','-movflags','+faststart',str(logo)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(SECONDS*FPS):
            proc.stdin.write(overlay(i/FPS).tobytes())
        proc.stdin.close()
        assert proc.wait()==0
    finally:
        if proc.poll() is None:proc.terminate();proc.wait()
    listing=out/'concat.txt'
    listing.write_text(f"file '{logo}'\nfile '{source}'\n",encoding='utf-8')
    final=out/'drivetto-introduction-logo.mp4'
    run('-f','concat','-safe','0','-i',listing,'-map','0:v:0','-c','copy','-an','-movflags','+faststart',final)
    print('Five-second logo opening joined to original video',flush=True)
    run('-ss','3.4','-i',logo,'-frames:v','1','-q:v','2',out/'intro-logo-poster.jpg')
    run('-ss','0.25','-i',logo,'-t','4.15','-filter_complex','fps=10,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0','-threads','3',out/'intro-logo-teaser.gif')
    run('-i',final,'-f','null','-')

    # Compare every decoded frame after the five-second insert with the old movie.
    run('-i',source,'-map','0:v:0','-f','framemd5',out/'original.framemd5')
    run('-i',final,'-vf',f'trim=start_frame={FPS*SECONDS},setpts=PTS-STARTPTS','-map','0:v:0','-f','framemd5',out/'tail.framemd5')
    def framehashes(p):
        return [s.split(',')[-1].strip() for s in p.read_text().splitlines() if s and not s.startswith('#')]
    original_hashes=framehashes(out/'original.framemd5');tail_hashes=framehashes(out/'tail.framemd5')
    assert len(original_hashes)==2736 and original_hashes==tail_hashes
    probe=info(final);assert float(probe['format']['duration'])==119
    assert int(probe['streams'][0]['nb_frames'])==2856
    # Existing chapters receive a fixed offset; no content inside those chapters moves.
    old=(root/'docs/assets/videos/drivetto-introduction.vtt').read_text()
    def shift(match):
        h,m,s,ms=map(int,match.groups());n=h*3600+m*60+s+SECONDS
        return f'{n//3600:02}:{n%3600//60:02}:{n%60:02}.{ms:03}'
    shifted=re.sub(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})',shift,old.split('WEBVTT',1)[1].strip())
    (out/'drivetto-introduction-logo.vtt').write_text('WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nDriveTTO | Logo opening\n\n'+shifted+'\n',encoding='utf-8')
    # Contact sheet includes the reveal, hold, transition and the untouched cartoon.
    frames=[]
    for i,t in enumerate([.5,1.3,2.2,3.4,4.75,5.25]):
        p=out/f'preview-{i}.jpg';run('-ss',t,'-i',final,'-frames:v','1','-q:v','2',p)
        im=Image.open(p).convert('RGB').resize((640,360));frames.append(im)
    contact=Image.new('RGB',(1280,3*395),(255,249,237));d=ImageDraw.Draw(contact)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
    for i,im in enumerate(frames):
        x=(i%2)*640;y=(i//2)*395;contact.paste(im,(x,y));d.text((x+12,y+367),f'{[.5,1.3,2.2,3.4,4.75,5.25][i]:.2f} s',font=small,fill=(23,63,66))
    contact.save(out/'logo-contact-sheet.jpg',quality=92)
    files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in out.iterdir() if p.name in ['drivetto-logo-opening.mp4','drivetto-introduction-logo.mp4','intro-logo-poster.jpg','intro-logo-teaser.gif','drivetto-introduction-logo.vtt']}
    receipt={'source_sha256':sha(source),'source_duration_seconds':114,'intro_duration_seconds':5,'duration_seconds':119,'width':W,'height':H,'fps':FPS,'audio':'silent, as in original','original_decoded_frames_preserved':2736,'all_original_frames_identical':True,'full_decode_actual_exit':0,'files':files,'background_sources':provenance,'design':'Original dual-trajectory logo draw-on and wordmark over four moving HUGSIM front views; cream transition into the untouched original movie.','reference':'FPD project page opening structure, using only DriveTTO media and branding.'}
    (out/'LOGO_INTRO_RENDER.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
