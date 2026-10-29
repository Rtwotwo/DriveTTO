"""Bind a verified revised visual edit with relaxed piano; retain previous media."""
from pathlib import Path
import argparse
import copy
import hashlib
import html
import json
import shutil
import subprocess
from urllib.parse import quote

ROOT = Path('/data/xinyao/release/DriveTTO')
STAGE = ROOT / '.site-staging-20261030-piano-v1'
OLD_SRC = 'assets/videos/drivetto-introduction-five-minute-20261030.mp4'
NEW_SRC = 'assets/videos/drivetto-introduction-piano-20261030.mp4'
OLD_SHA = 'eb04e288ec0dadd2ddd5d8e9e6e15999a9d5e84bec0abd2a84390e2e5e0d548d'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--intro-json', type=Path,
                        default=STAGE / 'INTRO_VISUAL.json')
    args = parser.parse_args()
    receipt_path = STAGE / 'PUBLICATION_PREPARED.json'
    assert not receipt_path.exists(), 'This publication has already been prepared.'
    old_video = ROOT / 'docs' / OLD_SRC
    new_video = ROOT / 'docs' / NEW_SRC
    assert sha(old_video) == OLD_SHA
    new_sha = sha(new_video)
    qa = read_json(STAGE / 'VIDEO_QA.json')
    assert qa['original_file_sha256'] == OLD_SHA
    assert qa['new_file_sha256'] == new_sha
    assert qa['visual_source_video_stream_sha256'] == qa['new_video_stream_sha256']
    assert len(qa['visual_source_video_stream_sha256']) == 64
    assert qa['decode_exit_code'] == 0
    assert abs(float(qa['duration_seconds']) - 300.0) < 0.05
    probe = json.loads(subprocess.check_output([
        '/usr/bin/ffprobe', '-v', 'error', '-show_streams', '-show_format',
        '-of', 'json', str(new_video)
    ], text=True))
    assert abs(float(probe['format']['duration']) - 300.0) < 0.05
    videos = [x for x in probe['streams'] if x['codec_type'] == 'video']
    audios = [x for x in probe['streams'] if x['codec_type'] == 'audio']
    assert len(videos) == len(audios) == 1
    assert videos[0]['width'] == 1280 and videos[0]['height'] == 720
    assert audios[0]['codec_name'] == 'aac' and audios[0]['channels'] == 2

    music = read_json(STAGE / 'music.json')
    music['description'] = 'An original relaxed piano composition, rendered with acoustic upright-piano samples.'
    music['composition'] = 'Original composition for the DriveTTO five-minute introduction.'
    music['sample_bank'] = {
        'name': 'FreePats Upright Piano KW',
        'version': '2022-02-21',
        'instrument': 'Kawai upright piano',
        'recorded_by': 'Gonzalo and Roberto',
        'edited_by': 'Roberto',
        'source_url': 'https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html',
        'download_url': 'https://freepats.zenvoid.org/Piano/UprightPianoKW/UprightPianoKW-SFZ-20220221.7z',
        'license': 'CC0 1.0 Universal',
        'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/'
    }
    bank = STAGE / 'UprightPianoKW-complete.7z'
    if bank.is_file():
        music['sample_bank']['archive_sha256'] = sha(bank)

    intro_path = ROOT / 'docs/assets/data/intro-edit.json'
    old_intro = read_json(intro_path)
    assert old_intro['src'] == OLD_SRC and old_intro['sha256'] == OLD_SHA
    assert old_intro['duration_seconds'] == 300.0
    intro = read_json(args.intro_json)
    assert intro['duration_seconds'] == 300.0
    assert intro['chapters_src'] == 'assets/videos/drivetto-introduction-piano-20261030.vtt'
    chapter_file = ROOT / 'docs' / intro['chapters_src']
    assert chapter_file.is_file()
    intro['chapters_sha256'] = sha(chapter_file)
    intro.update(src=NEW_SRC, sha256=new_sha, bytes=new_video.stat().st_size, music=music)
    old_phrase = 'Original instrumental music accompanies the film;'
    if old_phrase in intro['selection']:
        intro['selection'] = intro['selection'].replace(
            old_phrase, 'Relaxed acoustic piano accompanies the film;')
    intro['previous_audio_edition'] = {'src': OLD_SRC, 'sha256': OLD_SHA}
    assert intro['source_results_sha256'] == old_intro['source_results_sha256']

    gallery = read_json(STAGE / 'GALLERY.json')
    assert isinstance(gallery, list) and len(gallery) == 10
    ids = [v['id'] for v in gallery]
    assert len(set(ids)) == len(ids)
    assert sum(v['difficulty'] == 'easy' for v in gallery) == 2
    gallery_files = []
    for v in gallery:
        for field, prefix, hash_field in [
            ('src', 'assets/videos/', 'web_sha256'),
            ('poster', 'assets/images/', 'poster_sha256')
        ]:
            rel = v[field]
            assert rel.startswith(prefix) and '..' not in Path(rel).parts
            target = ROOT / 'docs' / rel
            assert target.is_file(), 'Missing gallery media: ' + rel
            assert sha(target) == v[hash_field], 'Gallery media hash mismatch: ' + rel
            gallery_files.append('docs/' + rel)

    site_path = ROOT / 'docs/assets/data/site-data.json'
    old_site = read_json(site_path)
    site = copy.deepcopy(old_site)
    assert site['intro']['src'] == OLD_SRC and site['intro']['sha256'] == OLD_SHA
    site['intro'].update(src=NEW_SRC, sha256=new_sha, chapters=intro['chapters_src'])
    site['videos'] = gallery
    assert {k: v for k, v in site.items() if k not in {'intro', 'videos'}} == {
        k: v for k, v in old_site.items() if k not in {'intro', 'videos'}}

    selection_path = ROOT / 'docs/assets/data/media-selection.json'
    old_selection = read_json(selection_path)
    selection = copy.deepcopy(old_selection)
    assert selection['intro']['src'] == OLD_SRC
    selection['intro'] = intro
    archived = {v['id']: v for v in selection.get('archived_videos', [])}
    archived.update({v['id']: v for v in selection['videos'] if v['id'] not in ids})
    for current_id in ids:
        archived.pop(current_id, None)
    selection['archived_videos'] = list(archived.values())
    selection['videos'] = gallery
    mutable = {'intro', 'videos', 'archived_videos'}
    assert {k: v for k, v in selection.items() if k not in mutable} == {
        k: v for k, v in old_selection.items() if k not in mutable}

    index = (ROOT / 'docs/index.html').read_text(encoding='utf-8')
    assert index.count(OLD_SRC) == 2
    index = index.replace(OLD_SRC, NEW_SRC)
    assert index.count(old_intro['chapters_src']) == 1
    index = index.replace(old_intro['chapters_src'], intro['chapters_src'])
    original_readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    readme = original_readme
    assert readme.count('Play the DriveTTO introduction with original music') == 1
    readme = readme.replace('Play the DriveTTO introduction with original music',
                            'Play the DriveTTO introduction with relaxed piano music')
    caption = '5 min 0 s · Method · Planning · Closed-loop driving —'
    assert readme.count(caption) == 1
    readme = readme.replace(caption, '5 min 0 s · Relaxed piano · Method · Planning · Closed-loop driving —')
    start_heading = '### 🛣️ HUGSIM closed-loop rollouts'
    end_heading = '### 🧭 NAVSIM planning animations'
    gallery_start, gallery_end = readme.index(start_heading), readme.index(end_heading)
    rows = [start_heading, '', '<table align="center">', '<tbody>']
    for i, v in enumerate(gallery):
        if i % 3 == 0:
            rows.append('<tr>')
        link = 'https://rtwotwo.github.io/DriveTTO/player.html?v=' + quote(v['id'], safe='')
        label = (f"{v['dataset']} · {v['difficulty']} · {float(v['duration']):g} s"
                 f" · RC {float(v['rc']):.1f} · HD {float(v['hd']):.1f}")
        rows.append(
            '<td align="center"><a href="' + html.escape(link, quote=True)
            + '"><img src="docs/' + html.escape(v['poster'], quote=True)
            + '" width="320" alt="' + html.escape(v['title'], quote=True)
            + '"></a><p align="left"><strong>' + html.escape(v['title'])
            + '</strong><br><em>' + html.escape(label) + '</em></p></td>'
        )
        if i % 3 == 2 or i == len(gallery) - 1:
            rows.append('</tr>')
    rows += ['</tbody>', '</table>', '', '']
    readme = readme[:gallery_start] + '\n'.join(rows) + readme[gallery_end:]
    assert readme[readme.index(end_heading):] == original_readme[original_readme.index(end_heading):]
    assert readme[:readme.index('## 🎬 Visualizations')] == original_readme[:original_readme.index('## 🎬 Visualizations')]

    updates = {
        'README.md': readme.encode('utf-8'),
        'docs/index.html': index.encode('utf-8'),
        'docs/assets/data/site-data.json': json_bytes(site),
        'docs/assets/data/media-selection.json': json_bytes(selection),
        'docs/assets/data/intro-edit.json': json_bytes(intro),
        'docs/assets/data/piano-music.json': json_bytes(music),
    }
    before = {}
    for rel in list(updates) + ['WEBSITE_MANIFEST.json']:
        target = ROOT / rel
        before[rel] = sha(target) if target.exists() else None
        if target.exists():
            backup = STAGE / 'before' / rel
            assert not backup.exists(), 'Existing publication backup: ' + rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
    for rel, body in updates.items():
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)

    changed = list(updates) + [
        'docs/' + NEW_SRC, 'docs/' + intro['chapters_src'], 'tools/publish_piano_intro.py',
        'tools/generate_leisure_piano.py', 'tools/render_piano_hard_edit.py', 'tools/mux_piano_intro.py'
    ] + gallery_files
    changed = list(dict.fromkeys(changed))
    manifest = read_json(ROOT / 'WEBSITE_MANIFEST.json')
    by_path = {x['path']: x for x in manifest['files']}
    for rel in changed:
        target = ROOT / rel
        assert target.is_file(), 'Missing publication file: ' + rel
        by_path[rel] = {'path': rel, 'bytes': target.stat().st_size, 'sha256': sha(target)}
    manifest['files'] = [by_path[key] for key in sorted(by_path)]
    (ROOT / 'WEBSITE_MANIFEST.json').write_bytes(json_bytes(manifest))
    changed.append('WEBSITE_MANIFEST.json')
    receipt = {
        'task': 'Publish the revised five-minute introduction with relaxed piano',
        'duration_seconds': 300.0,
        'revised_visual_source_stream_preserved_during_audio_mux': True,
        'original_video_sha256': OLD_SHA,
        'new_video_sha256': new_sha,
        'video_qa': qa,
        'before_sha256': before,
        'changed_files': changed,
        'files': [{'path': rel, 'bytes': (ROOT / rel).stat().st_size,
                   'sha256': sha(ROOT / rel)} for rel in changed],
        'aggregate_results_and_navsim_layout_preserved': True,
        'gallery_revised': True,
        'active_gallery_count': len(gallery),
        'active_easy_gallery_count': sum(v['difficulty'] == 'easy' for v in gallery),
        'archived_gallery_count': len(archived),
        'previous_gallery_links_preserved': True,
        'gallery_metadata_sha256': sha(STAGE / 'GALLERY.json'),
        'visual_edit_metadata_path': str(args.intro_json),
        'visual_edit_metadata_sha256': sha(args.intro_json),
    }
    receipt_path.write_bytes(json_bytes(receipt))
    (STAGE / 'INTRO.json').write_bytes(json_bytes(intro))
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
