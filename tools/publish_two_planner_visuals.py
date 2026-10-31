"""Prepare two-planner labels and detailed street actors for the existing website."""
from pathlib import Path
import copy,hashlib,json,shutil,subprocess
R=Path('/data/xinyao/release/DriveTTO');S=R/'.method-planners-20261031-v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def jb(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
changed=[]
def put(rel,body):
 p=R/rel;b=S/'before'/rel
 if p.exists():
  assert not b.exists(),rel
  b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body);changed.append(rel)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='43076ed3f86cad3976f5169dccd646b56c04069f'
qa=read(S/'ASSEMBLY.json');assert qa['complete_decode_exit_codes']==[0,0,0]
for k in ['public','review','method']:assert sha(S/qa[k]['name'])==qa[k]['sha256']
site=read(R/'docs/assets/data/site-data.json');sel=read(R/'docs/assets/data/media-selection.json');intro=read(R/'docs/assets/data/intro-edit.json')
assert intro['sha256']==qa['old_intro_sha256']
fixedsite=copy.deepcopy({k:v for k,v in site.items() if k not in ['intro','method']})
fixedsel=copy.deepcopy({k:v for k,v in sel.items() if k not in ['intro','algorithm_animation']})
oldintro=intro['src'];oldanim=copy.deepcopy(site['method']['animation'])
newintro='assets/videos/'+qa['public']['name'];newmethod='assets/videos/'+qa['method']['name']
poster='assets/images/method-two-planners-20261031.jpg';gif='assets/images/method-two-planners-20261031.gif'
ichap='assets/videos/intro-two-planners-20261031-chapters.vtt';mchap='assets/videos/method-two-planners-20261031-chapters.vtt';mcap='assets/videos/method-two-planners-20261031-captions.vtt'
for rel,name in {newintro:qa['public']['name'],newmethod:qa['method']['name'],poster:'method-poster.jpg',gif:'method-teaser.gif',ichap:'intro-chapters.vtt',mchap:'method-chapters.vtt',mcap:'method-captions.vtt'}.items():put('docs/'+rel,(S/name).read_bytes())
note='A continuous NAV1 Full illustration: full-path utility guides endpoint requests; proposals from two frozen planners establish a shared center; bounded refinement and temporal fusion adjust the complete motion. Geometry, utility colors and perturbations are schematic.'
anim=dict(src=newmethod,poster=poster,captions=mcap,chapters=mchap,duration_seconds=168,sha256=qa['method']['sha256'],scope=oldanim['scope'],note=note)
site['method']['animation']=anim;sel['algorithm_animation']=anim
intro.update(src=newintro,sha256=qa['public']['sha256'],bytes=qa['public']['bytes'],poster=poster,poster_sha256=sha(R/'docs'/poster),teaser=gif,teaser_sha256=sha(R/'docs'/gif),chapters_src=ichap,chapters_sha256=sha(R/'docs'/ichap))
intro['previous_edition']={'src':oldintro,'sha256':qa['old_intro_sha256'],'duration_seconds':396}
site['intro'].update(src=newintro,poster=poster,sha256=qa['public']['sha256'],chapters=ichap)
sel['intro']=intro
assert fixedsite=={k:site[k] for k in fixedsite}
assert fixedsel=={k:sel[k] for k in fixedsel}
for name,x in [('site-data.json',site),('media-selection.json',sel),('intro-edit.json',intro)]:put('docs/assets/data/'+name,jb(x))
index=(R/'docs/index.html').read_text()
for a,b in [(oldintro,newintro),(oldanim['src'],newmethod),(oldanim['poster'],poster),(oldanim['chapters'],mchap),(oldanim['captions'],mcap),('assets/videos/intro-continuous-20261031-chapters.vtt',ichap)]:
 assert a in index,a
 index=index.replace(a,b)
put('docs/index.html',index.encode())
readme=(R/'README.md').read_text()
assert 'proposals from ChainFlow and DrivoR then establish' in readme
readme=readme.replace('proposals from ChainFlow and DrivoR then establish','proposals from two frozen planners then establish')
readme=readme.replace('docs/assets/images/method-continuous-20261031.gif','docs/'+gif)
put('README.md',readme.encode())
prov=read(R/'docs/assets/data/continuous-method-20261031.json')
prov.update(two_planners=['Planner 1','Planner 2'],render_sha256=qa['source_sha256'],method_video_sha256=qa['method']['sha256'],public_video_sha256=qa['public']['sha256'],actor_art=qa['actor_art'],vehicle_footprint_dimensions_unchanged=True)
put('docs/assets/data/continuous-method-20261031.json',jb(prov))
changed.extend(['tools/render_continuous_method.py','tools/assemble_two_planner_visuals.py','tools/publish_two_planner_visuals.py'])
manifest=read(R/'WEBSITE_MANIFEST.json');by={x['path']:x for x in manifest['files']}
for rel in changed:by[rel]={'path':rel,'bytes':(R/rel).stat().st_size,'sha256':sha(R/rel)}
manifest['files']=[by[k] for k in sorted(by)];put('WEBSITE_MANIFEST.json',jb(manifest))
for p in [R/'docs'/newintro,R/'docs'/newmethod]:assert p.stat().st_size<100_000_000
subprocess.run(['git','diff','--check'],cwd=R,check=True)
receipt={'files':[{'path':p,'sha256':sha(R/p),'bytes':(R/p).stat().st_size} for p in changed],'result_tables_and_gallery_unchanged':True,'ready_for_commit':True}
(S/'PUBLICATION_PREPARED.json').write_bytes(jb(receipt));print(json.dumps(receipt),flush=True)
