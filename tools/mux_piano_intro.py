"""Mix the relaxed acoustic piano score and verify the revised film."""
from pathlib import Path
import subprocess,json,hashlib,re
R=Path('/data/xinyao/release/DriveTTO');S=R/'.site-staging-20261030-piano-v1'
old=R/'docs/assets/videos/drivetto-introduction-five-minute-20261030.mp4'
visual=S/'edit/silent.mp4';dest=R/'docs/assets/videos/drivetto-introduction-piano-20261030.mp4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def streamsha(p):
 return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-c','copy','-f','hash','-hash','sha256','-'],text=True).strip().split('=')[1]
first=(S/'loudness-pass1.log').read_text();stats=json.loads(first[first.rfind('{'):])
af='loudnorm=I=-21:TP=-2:LRA=8:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true:print_format=json'.format(**stats)
assert visual.exists() and not dest.exists()
with (S/'mux.log').open('w') as f:
 subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(visual),'-i',str(S/'leisure-piano.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',af,'-ar','48000','-c:a','aac','-b:a','192k','-t','300','-movflags','+faststart',str(dest)],check=True,stderr=f)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)],text=True))
decoded=subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'],capture_output=True,text=True)
assert decoded.returncode==0 and not decoded.stderr
visualsha=streamsha(visual);finalsha=streamsha(dest);assert visualsha==finalsha
assert float(probe['format']['duration'])==300
music=json.loads((S/'music.json').read_text())
music['mastering']={'target_lufs':-21,'true_peak_ceiling_dbtp':-2,'loudness_range_target':8,'first_pass':stats,'method':'two-pass loudnorm with linear normalization'}
(S/'music.json').write_text(json.dumps(music,ensure_ascii=False,indent=2)+'\n')
qa=dict(original_file_sha256=sha(old),new_file_sha256=sha(dest),visual_source_video_stream_sha256=visualsha,new_video_stream_sha256=finalsha,duration_seconds=300.0,decode_exit_code=decoded.returncode,decode_errors=decoded.stderr,bytes=dest.stat().st_size,probe=probe)
(S/'VIDEO_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in qa.items() if k!='probe'},indent=2))
