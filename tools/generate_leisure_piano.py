"""Original relaxed solo-piano accompaniment; no drums, pads or quoted melody.

The default renderer uses a damped, slightly inharmonic multi-string piano model.
Optionally supply actual piano WAV samples with --sample-dir. Filenames such as
C4.wav, Fs3.wav, A0v4.wav are recognized; samples.json may instead contain a list
of {"file": "relative.wav", "midi": 60}. Sample licensing remains the caller's
responsibility and the source files are recorded in the output metadata.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import wave
import numpy as np

SR=48000
BPM=72
BEAT=60.0/BPM
BAR=4*BEAT
SEED=20261030
# Common major-key harmony, arranged here with an original short melodic phrase.
# Each tuple holds bass, broken-chord voicing, and a four-note melodic contour.
PROGRESSION=[
 (36,[48,55,59,62,64],[76,74,71,72]),
 (35,[47,55,59,62,67],[74,71,69,67]),
 (33,[45,52,55,60,64],[72,71,69,67]),
 (41,[53,57,60,64,67],[69,72,76,74]),
 (40,[52,55,60,64,67],[76,74,72,71]),
 (38,[50,57,60,64,65],[74,72,69,65]),
 (31,[43,55,59,62,65],[71,69,67,74]),
 (36,[48,55,60,64,69],[72,69,67,64]),
]


def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()


def read_pcm(path):
 with wave.open(str(path),'rb') as f:
  channels=f.getnchannels();rate=f.getframerate();width=f.getsampwidth()
  if f.getcomptype()!='NONE':raise ValueError('Only uncompressed PCM WAV samples are supported')
  raw=f.readframes(f.getnframes())
 if width==1:x=(np.frombuffer(raw,np.uint8).astype(np.float32)-128)/128
 elif width==2:x=np.frombuffer(raw,'<i2').astype(np.float32)/32768
 elif width==3:
  a=np.frombuffer(raw,np.uint8).reshape(-1,3).astype(np.int32)
  z=a[:,0]|(a[:,1]<<8)|(a[:,2]<<16);z=(z^(1<<23))-(1<<23)
  x=z.astype(np.float32)/8388608
 elif width==4:x=np.frombuffer(raw,'<i4').astype(np.float32)/2147483648
 else:raise ValueError('Unsupported PCM sample width')
 x=x.reshape(-1,channels).mean(axis=1)
 if not len(x) or not np.all(np.isfinite(x)):raise ValueError('Empty or invalid sample')
 return x,rate


def load_samples(folder):
 if folder is None:return {},[]
 folder=Path(folder).resolve(strict=True)
 mapping=[];manifest=folder/'samples.json'
 if manifest.exists():mapping=json.loads(manifest.read_text(encoding='utf-8-sig'))
 else:
  names={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
  for p in sorted(folder.rglob('*.wav')):
   match=re.search(r'(?:^|[_ -])([A-Ga-g])([#bs]?)(-?\d)(?:v\d+)?(?:[_ .-]|$)',p.name)
   if match:
    note,acc,octave=match.groups();pitch=12*(int(octave)+1)+names[note.upper()]+({'#':1,'s':1,'b':-1,'':0}[acc])
    mapping.append({'file':p.relative_to(folder).as_posix(),'midi':pitch})
 if not mapping:raise ValueError('No note-named WAV files or samples.json found')
 samples={};sources=[]
 for item in mapping:
  midi=int(item['midi']);p=(folder/item['file']).resolve(strict=True)
  if not p.is_relative_to(folder) or not 0<=midi<=127:raise ValueError('Invalid sample mapping')
  if midi in samples:continue
  x,rate=read_pcm(p);samples[midi]=(x,rate)
  sources.append({'file':p.name,'midi':midi,'sha256':digest(p),'sample_rate_hz':rate})
 return samples,sources


class Piano:
 def __init__(self,samples):self.samples=samples;self.cache={}
 def tone(self,midi):
  if midi in self.cache:return self.cache[midi]
  length=7.0 if midi<48 else (5.2 if midi<65 else 3.8)
  if self.samples:
   root=min(self.samples,key=lambda k:abs(k-midi));sample,rate=self.samples[root]
   positions=np.arange(round(length*SR),dtype=np.float64)*(rate/SR)*2**((midi-root)/12)
   x=np.interp(positions,np.arange(len(sample)),sample,left=0,right=0).astype(np.float32)
   peak=float(np.max(np.abs(x)))
   if peak>0:x*=.7/peak
  else:
   t=np.arange(round(length*SR),dtype=np.float32)/SR
   f=440*2**((midi-69)/12);x=np.zeros(len(t),np.float32)
   # Piano upper partials lose energy more quickly than the low vibrating modes.
   stiffness=.000045*2**((midi-48)/24)
   sustain=2.8*2**((55-midi)/34)
   for harmonic in range(1,min(24,int(16000/f))+1):
    freq=f*harmonic*math.sqrt(1+stiffness*harmonic*harmonic)
    amp=(.65+.35*abs(math.sin(harmonic*.137*math.pi)))/harmonic**1.28
    decay=np.exp(-t/(.16+sustain/harmonic**.88))
    # A soft hammer produces a fast attack without a synthetic sustained pad.
    attack=1-np.exp(-t/(.0025+.005/harmonic))
    for cents,weight in [(-.8,.26),(0,.48),(.9,.26)]:
     x+=(amp*weight*np.sin(2*math.pi*freq*2**(cents/1200)*t)*decay*attack).astype(np.float32)
   rng=np.random.default_rng(SEED+midi)
   n=min(round(.055*SR),len(t));noise=rng.standard_normal(n).astype(np.float32)
   noise=np.convolve(noise,np.ones(7,dtype=np.float32)/7,mode='same')
   x[:n]+=.018*noise*(1-np.exp(-t[:n]/.0006))*np.exp(-t[:n]/.012)
   peak=float(np.max(np.abs(x)))
   if peak>0:x*=.7/peak
  self.cache[midi]=x
  return x


def compose(seconds=300.0):
 if not math.isfinite(seconds) or not .1<=seconds<=600:raise ValueError('Duration must be between .1 and 600 seconds')
 rng=np.random.default_rng(SEED);events=[];bars=int(math.ceil(seconds/BAR))
 def add(start,pitch,gate,velocity,role):
  if start>=seconds-.4:return
  if role!='cadence':start=max(0,start+float(rng.uniform(-.018,.018)))
  velocity=float(np.clip(velocity+rng.uniform(-.025,.025),.2,.75))
  events.append((start,int(pitch),float(gate),velocity,role))
 for bar in range(bars):
  start=bar*BAR
  if bar>=bars-3:
   # ii–V–I ending, with space for the final tonic to decay naturally.
   bass,chord,melody=PROGRESSION[[5,6,7][bar-(bars-3)]]
   for j,pitch in enumerate([bass,*chord[:-1]]):add(start+j*.025,pitch,4.8,.41 if j==0 else .33,'cadence')
   if bar<bars-1:add(start+BEAT*1.8,melody[-1],1.1,.47,'cadence')
   else:
    add(start+.12,72,3.8,.45,'cadence')
    add(start+.18,76,3.8,.35,'cadence')
   continue
  bass,chord,melody=PROGRESSION[bar%len(PROGRESSION)]
  # Long phrases breathe in four-bar waves; the harmony remains light and major.
  phrase=.94+.06*math.sin((bar%16)/16*2*math.pi)
  introduction=.82 if start<17.75 else 1.0
  velocity=phrase*introduction
  add(start,bass,2.2,.40*velocity,'bass')
  if bar%4!=3:add(start+2*BEAT,bass+12,1.5,.28*velocity,'bass')
  order=[0,2,1,3] if (bar//8)%2==0 else [0,1,3,2]
  for j,index in enumerate(order):
   add(start+(.45+j)*BEAT,chord[index],1.15,.31*velocity,'arpeggio')
  pattern=(bar//4)%4
  if pattern==0:notes=[(0,1.45,0),(1.8,.7,1),(2.8,1.05,2)]
  elif pattern==1:notes=[(0,2.2,0),(2.5,1.35,3)]
  elif pattern==2:notes=[(0,.85,2),(1.0,.85,1),(2,1.8,0)]
  else:notes=[(.25,2.7,3)]
  for offset,length,index in notes:
   pitch=melody[index]
   # A middle-register variation changes the color every third eight-bar phrase.
   if (bar//8)%3==2:pitch-=12
   add(start+offset*BEAT,pitch,length*BEAT,.52*velocity,'melody')
 return events


def render(seconds=300.0,sample_dir=None):
 samples,sources=load_samples(sample_dir);piano=Piano(samples);events=compose(seconds)
 count=round(seconds*SR);audio=np.zeros((count,2),np.float32)
 for start,midi,gate,velocity,role in events:
  source=piano.tone(midi);first=round(start*SR);n=min(len(source),count-first)
  if n<=0:continue
  t=np.arange(n,dtype=np.float32)/SR
  # Gentle pedal overlap, followed by damper release. No sustained oscillator.
  release=.65 if role not in ('cadence','bass') else 1.2
  damping=np.exp(-np.maximum(0,t-gate)/release)
  sound=source[:n]*damping*(velocity**1.3)*.42
  pan=float(np.clip((midi-60)/48,-.45,.45));angle=(pan+1)*math.pi/4
  audio[first:first+n,0]+=sound*math.cos(angle)
  audio[first:first+n,1]+=sound*math.sin(angle)
 # Restrained room reflections; the dry instrument remains dominant.
 dry=audio.copy()
 for delay,gain,cross in [(.021,.06,False),(.037,.052,True),(.061,.038,False),(.101,.031,True),(.167,.025,False),(.263,.018,True),(.389,.013,False)]:
  offset=round(delay*SR)
  if offset<count:audio[offset:]+=dry[:-offset,::-1] * gain if cross else dry[:-offset]*gain
 del dry
 t=np.arange(count,dtype=np.float32)/SR
 fadein=np.sin(np.clip(t/1.5,0,1)*math.pi/2)**2
 fadeout=np.sin(np.clip((count-1-np.arange(count,dtype=np.float32))/SR/3,0,1)*math.pi/2)**2
 audio-=np.mean(audio,axis=0,dtype=np.float64).astype(np.float32)
 audio*=(fadein*fadeout)[:,None]
 peak=float(np.max(np.abs(audio)));gain=min(2.5,.70/peak) if peak else 1
 audio*=gain
 assert np.all(np.isfinite(audio)) and float(np.max(np.abs(audio)))<=.70001
 metadata={'title':'An Unhurried Drive','style':'Relaxed solo piano','composition':'Original arrangement and melody generated for the DriveTTO film',
  'rendering':'Recorded piano WAV samples' if samples else 'Damped multi-string piano synthesis',
  'bpm':BPM,'seed':SEED,'instruments':['piano'],'vocals':False,'drums':False,'pads':False,
  'sample_rate_hz':SR,'channels':2,'duration_seconds':count/SR,'sample_frames':count,
  'note_count':len(events),'cached_pitches':len(piano.cache),'sources':sources,
  'source_audio_samples_used':bool(samples),'fade_in_seconds':1.5,'fade_out_seconds':3,
  'ending':'ii–V–I cadence over the final three bars, with the final tonic left to decay',
  'peak':float(np.max(np.abs(audio))),'rms':float(np.sqrt(np.mean(audio.astype(np.float64)**2))),
  'render_gain':gain,'clipped_samples':0,'mastering':'Apply final video loudness normalization separately; intended background target around -21 LUFS.'}
 return audio,metadata


def write(seconds,output,metadata,sample_dir=None):
 output=Path(output);metadata=Path(metadata)
 if output.resolve()==metadata.resolve():raise ValueError('Audio and metadata paths must differ')
 if output.exists() or metadata.exists():raise FileExistsError('Refusing to overwrite prior output')
 audio,info=render(seconds,sample_dir)
 output.parent.mkdir(parents=True,exist_ok=True);metadata.parent.mkdir(parents=True,exist_ok=True)
 pcm=np.rint(audio*32767).astype('<i2')
 assert not np.any(np.abs(pcm.astype(np.int32))>=32767)
 with wave.open(str(output),'wb') as f:
  f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes(pcm.tobytes())
 info.update(format='PCM16 WAV',bytes=output.stat().st_size,sha256=digest(output))
 metadata.write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 return info


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--seconds',type=float,default=300)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--metadata',type=Path,required=True)
 p.add_argument('--sample-dir',type=Path)
 a=p.parse_args();print(json.dumps(write(a.seconds,a.output,a.metadata,a.sample_dir),ensure_ascii=False))


if __name__=='__main__':main()
