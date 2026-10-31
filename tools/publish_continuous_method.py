"""Prepare the reviewed continuous-animation release; commit is a separate step."""
from pathlib import Path
import copy,hashlib,json,shutil,subprocess
R=Path('/data/xinyao/release/DriveTTO');S=R/'.method-continuous-20261031-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def jb(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def put(rel,body):
 p=R/rel;b=S/'before'/rel
 if p.exists():
  assert not b.exists(),f'Already prepared: {rel}'
  b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body);changed.append(rel)
qa=read(S/'ASSEMBLY.json');assert qa['complete_decode_exit_codes']==[0,0,0]
changed=[]
newintro='assets/videos/'+qa['public']['name'];newmethod='assets/videos/'+qa['method']['name']
poster='assets/images/method-continuous-20261031.jpg';gif='assets/images/method-continuous-20261031.gif'
ichap='assets/videos/intro-continuous-20261031-chapters.vtt';mchap='assets/videos/method-continuous-20261031-chapters.vtt';mcap='assets/videos/method-continuous-20261031-captions.vtt'
media={newintro:qa['public']['name'],newmethod:qa['method']['name'],poster:'method-poster.jpg',gif:'method-continuous-teaser.gif',ichap:'intro-chapters.vtt',mchap:'method-chapters.vtt',mcap:'method-captions.vtt'}
for rel,name in media.items():put('docs/'+rel,(S/name).read_bytes())
site=read(R/'docs/assets/data/site-data.json');sel=read(R/'docs/assets/data/media-selection.json');intro=read(R/'docs/assets/data/intro-edit.json')
fixed=copy.deepcopy({k:site[k] for k in site if k not in ['intro','method']})
oldintro=intro['src'];oldmethod=site['method']['animation']['src'];oldposter=site['method']['animation']['poster'];oldchap=site['method']['animation']['chapters'];oldcap=site['method']['animation']['captions']
assert intro['sha256']==qa['old_intro_sha256']
note='A continuous NAV1 Full illustration: full-path utility guides endpoint requests; ChainFlow and DrivoR proposals establish a shared center; bounded refinement and temporal fusion adjust the complete motion. Geometry, utility colors and perturbations are schematic.'
anim=dict(src=newmethod,poster=poster,captions=mcap,chapters=mchap,duration_seconds=168,sha256=qa['method']['sha256'],scope='NAV1 Full continuous schematic; benchmark schedules differ',note=note)
site['method']['animation']=anim;sel['algorithm_animation']=anim
intro.update(src=newintro,duration_seconds=396,sha256=qa['public']['sha256'],bytes=qa['public']['bytes'],chapters=qa['chapters'],chapters_src=ichap,chapters_sha256=sha(R/'docs'/ichap),poster=poster)
intro['selection']='A 6-minute 36-second introduction: one continuous endpoint-search and dual-planner refinement demonstration, four NAVSIM plans at PDMS 100, and the previously selected ten complete HUGSIM episodes at original speed. Relaxed piano accompanies the film. Method geometry and utility are schematic; scene scores belong to their complete recorded episodes.'
intro['previous_edition']={'src':oldintro,'sha256':qa['old_intro_sha256'],'duration_seconds':300}
intro['music']['duration_seconds']=396;intro['music']['edit']='Existing relaxed piano recording, extended with an internal passage and two 2-second crossfades.'
site['intro'].update(src=newintro,poster=poster,duration=396,sha256=qa['public']['sha256'],chapters=ichap)
sel['intro']=intro
assert fixed=={k:site[k] for k in fixed}
for name,x in [('site-data.json',site),('media-selection.json',sel),('intro-edit.json',intro)]:put('docs/assets/data/'+name,jb(x))
index=(R/'docs/index.html').read_text();index=index.replace(oldintro,newintro).replace('assets/videos/drivetto-introduction-piano-20261030.vtt',ichap)
index=index.replace('5 min 0 s · Method · Planning · Closed-loop driving','6 min 36 s · Endpoint search · Refinement · Driving').replace('assets/images/intro-recut-20261030.jpg',poster)
index=index.replace(oldmethod,newmethod).replace(oldposter,poster).replace(oldchap,mchap).replace(oldcap,mcap)
index=index.replace('<h3>Search. Compare. Select.</h3>','<h3>From endpoint search to precise motion.</h3>')
index=index.replace('A 72-second, illustrated walkthrough of the NAV1 Full schedule.','A continuous 2-minute 48-second illustration of endpoint feedback and two-planner refinement.')
index=index.replace('DriveTTO algorithm explained through a 2D cartoon','DriveTTO continuous endpoint search and trajectory refinement')
index=index.replace('Follow the retained plan through endpoint feedback, bounded refinement, shared-context scoring and branch fusion. Paths and predicted gains are schematic.','Watch complete-path evaluations reveal a promising endpoint region, then follow the two planners through local refinement and matched-time fusion. Close-ups show how small position changes affect vehicle clearance. Geometry and utility are schematic.')
put('docs/index.html',index.encode())
player=(R/'docs/player.js').read_text();assert '["72 s", "Search. Compare. Select."]' in player
player=player.replace('["72 s", "Search. Compare. Select."]','[d.algorithm_animation.duration_seconds + " s", "Endpoint search → trajectory refinement"]')
put('docs/player.js',player.encode())
readme=(R/'README.md').read_text();readme=readme.replace('docs/assets/images/algorithm-teaser.gif','docs/'+gif).replace('docs/assets/images/intro-recut-20261030.gif','docs/'+gif)
readme=readme.replace('5 min 0 s · Relaxed piano · Method · Planning · Closed-loop driving','6 min 36 s · Relaxed piano · Endpoint search · Refinement · Driving')
readme=readme.replace('The animation below illustrates how DriveTTO searches and selects around a retained complete plan at test time.','The animation follows one road scene from endpoint search to fine trajectory refinement, with enlarged vehicle footprints showing why small position and timing changes matter.')
old='Concretely, endpoint feedback associates the predicted utility of a complete trajectory with its achieved terminal state, guiding further search through the planner\'s native path geometry. Geometric refinement, cross-model proposals and bounded control residuals produce alternative motions around the retained plan. Frozen scorers evaluate gains over the reference in a shared scoring context, and temporal fusion combines proposal and control trajectories along the prediction horizon. Each accepted update becomes the reference for later decisions. By separating the best trajectory available in a candidate pool from the trajectory actually returned, DriveTTO examines how candidate construction, filtering and ranking contribute to the final driving result.'
new='DriveTTO first completes endpoint requests through native path geometry, scores each full trajectory, and records that utility at the terminal state actually reached. Feedback from nearby reached states guides later requests toward promising regions. The accepted endpoint plan and proposals from ChainFlow and DrivoR then establish a shared trajectory center. Geometric adjustments, cross-model proposals and bounded control residuals refine the complete motion; temporal fusion combines branch contributions at matching future timestamps. Configured scorers compare each candidate with its current reference, which remains available whenever an update is rejected. The animation makes this sequence visible in one tight road scene, including magnified lateral clearance and longitudinal interaction geometry.'
assert old in readme;readme=readme.replace(old,new);put('README.md',readme.encode())
website=(R/'WEBSITE.md').read_text();website+='\n\nThe active introduction is 6:36 (2026-10-31). Its 2:48 method segment is a continuous NAV1 Full schematic linking endpoint utility feedback, two-planner refinement, matched-time fusion and vehicle-footprint close-ups. The selected HUGSIM and NAVSIM examples, their scores, and the qualitative image layouts are unchanged. Earlier media remain at their original URLs.\n'
put('WEBSITE.md',website.encode())
provenance={'duration_seconds':168,'intro_duration_seconds':396,'kind':'continuous_algorithm_schematic','scope':'NAV1 Full','paper_basis':['Endpoint completion and feedback','Bounded interpolation and geometric search','Cross-model proposal pool','Control residual transport','Branch fusion'],'utility':'Synthetic full-path utility archived at achieved states; XY projection of a position/heading/speed archive','small_offsets':'Illustrative geometry, not a measured safety experiment','two_planners':['ChainFlow','DrivoR'],'model_weights_changed':False,'experiments_executed':False,'real_gallery_and_result_tables_unchanged':True,'render_sha256':sha(R/'tools/render_continuous_method.py'),'method_video_sha256':qa['method']['sha256'],'public_video_sha256':qa['public']['sha256']}
put('docs/assets/data/continuous-method-20261031.json',jb(provenance))
changed.extend(['tools/render_continuous_method.py','tools/assemble_continuous_method.py','tools/publish_continuous_method.py'])
manifest=read(R/'WEBSITE_MANIFEST.json');by={x['path']:x for x in manifest['files']}
for rel in changed:by[rel]={'path':rel,'bytes':(R/rel).stat().st_size,'sha256':sha(R/rel)}
manifest['files']=[by[k] for k in sorted(by)];put('WEBSITE_MANIFEST.json',jb(manifest))
for path in [R/'docs'/newintro,R/'docs'/newmethod]:assert path.stat().st_size<100_000_000
subprocess.run(['git','diff','--check'],cwd=R,check=True)
receipt={'files':[{'path':p,'sha256':sha(R/p),'bytes':(R/p).stat().st_size} for p in changed],'original_gallery_and_result_tables_preserved':True,'previous_intro_preserved':sha(R/'docs'/oldintro)==qa['old_intro_sha256'],'ready_for_commit':True}
(S/'PUBLICATION_PREPARED.json').write_bytes(jb(receipt));print(json.dumps(receipt),flush=True)
