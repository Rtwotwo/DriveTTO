"""Replace only this task's unpublished short-cut bindings with the requested long cut."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
R=Path('/data/xinyao/release/DriveTTO');S=R/'.site-staging-20261030-recut-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=S/'PUBLICATION_PREPARED.json';receipt=json.loads(p.read_text());intro=json.loads((S/'INTRO.json').read_text())
assert intro['duration_seconds']==300 and sha(S/intro['src'])==intro['sha256']
current={x['path']:x['sha256'] for x in receipt['files']}
for rel,before in receipt['before_sha256'].items():
 if before is not None:
  assert sha(R/rel)==current[rel], 'Intervening edit: '+rel
  assert sha(S/'before'/rel)==before
shutil.copy2(p,S/'PUBLICATION_SHORT_PREVIEW.json')
for rel,before in receipt['before_sha256'].items():
 if before is not None:shutil.copy2(S/'before'/rel,R/rel)
# Short preview was never committed or pushed. Keep its media in staging.
archive=S/'unpublished-short';archive.mkdir(exist_ok=True)
for name in ['drivetto-introduction-recut-20261030.mp4','drivetto-introduction-recut-20261030.vtt']:
 source=R/'docs/assets/videos'/name
 assert source.is_file() and not (archive/name).exists()
 source.rename(archive/name)
subprocess.run([sys.executable,str(R/'tools/publish_recut_gallery.py')],check=True)
