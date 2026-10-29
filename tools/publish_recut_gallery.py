"""Bind a reviewed recut and gallery to the existing static site; never push Git.

Run on the release host after rendering GALLERY.json, INTRO.json and their
referenced media under .site-staging-20261030-recut-v1. Existing experiment
results, page layout, NAVSIM illustrations and old media are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from datetime import datetime, timezone
from urllib.parse import quote


BASE = "https://rtwotwo.github.io/DriveTTO/"
TEASER = "assets/images/intro-recut-20261030.gif"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def duration_label(seconds):
    seconds = round(float(seconds), 2)
    minutes = int(seconds // 60)
    remainder = f"{seconds - minutes * 60:g}"
    return f"{minutes} min {remainder} s" if minutes else f"{remainder} s"


def media_path(value):
    p = PurePosixPath(value)
    if (not isinstance(value, str) or p.is_absolute() or ".." in p.parts
            or not value.startswith(("assets/videos/", "assets/images/"))
            or "\\" in value or p.as_posix() != value):
        raise ValueError(f"Invalid relative media path: {value!r}")
    return value


def replace_once(text, old, new, name):
    if text.count(old) != 1:
        raise ValueError(f"Expected one {name}, found {text.count(old)}")
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/data/xinyao/release/DriveTTO"))
    parser.add_argument("--stage", type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    stage = (args.stage or root / ".site-staging-20261030-recut-v1").resolve(strict=True)
    docs = (root / "docs").resolve(strict=True)
    gallery = read(stage / "GALLERY.json")
    intro = read(stage / "INTRO.json")
    if not isinstance(gallery, list) or not gallery:
        raise ValueError("GALLERY.json must be a nonempty list")
    ids = [v["id"] for v in gallery]
    if len(ids) != len(set(ids)) or any(i in {"intro", "algorithm"} for i in ids):
        raise ValueError("Gallery IDs must be unique and must not use reserved IDs")
    duration = float(intro["duration_seconds"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Introduction duration must be positive and finite")
    for key in ("width", "height", "fps", "src", "poster", "chapters_src", "sha256",
                "poster_sha256", "bytes", "chapters", "title", "selection", "note"):
        if key not in intro:
            raise ValueError(f"Missing INTRO field: {key}")
    end = 0.0
    for chapter in intro["chapters"]:
        start, finish = float(chapter["start"]), float(chapter["end"])
        if abs(start - end) > 0.1 or finish <= start:
            raise ValueError("Introduction chapters must cover a continuous ordered timeline")
        end = finish
    if abs(end - duration) > 0.1:
        raise ValueError("Chapter timeline does not reach the introduction duration")

    payloads = {}
    source_assets = {}

    def asset(rel, expected_sha=None, expected_bytes=None):
        rel = media_path(rel)
        source = stage / rel
        # A retained asset may already be present in docs; it is never recoded here.
        if not source.is_file():
            source = docs / rel
        resolved = source.resolve(strict=True)
        if source.is_symlink() or not (resolved.is_relative_to(stage) or resolved.is_relative_to(docs)):
            raise ValueError(f"Media source escapes approved directories: {rel}")
        digest, size = sha(source), source.stat().st_size
        if expected_sha and digest != expected_sha:
            raise ValueError(f"SHA mismatch: {rel}")
        if expected_bytes is not None and size != expected_bytes:
            raise ValueError(f"Size mismatch: {rel}")
        source_assets[rel] = {"source": str(source), "sha256": digest, "bytes": size}
        payloads["docs/" + rel] = source

    for v in gallery:
        for key in ("dataset", "scene", "difficulty", "mode", "rc", "hd", "pdms",
                    "frames", "duration", "src", "poster", "title", "description",
                    "source_sha256", "web_sha256", "web_bytes"):
            if key not in v:
                raise ValueError(f"Missing {key} for {v['id']}")
        for key in ("rc", "hd"):
            if not math.isfinite(float(v[key])) or not 0 <= float(v[key]) <= 100:
                raise ValueError(f"Invalid {key} for {v['id']}")
        if float(v["duration"]) <= 0 or int(v["frames"]) <= 0:
            raise ValueError(f"Invalid duration or frames for {v['id']}")
        asset(v["src"], v["web_sha256"], v["web_bytes"])
        asset(v["poster"], v.get("poster_sha256"))
    asset(intro["src"], intro["sha256"], intro["bytes"])
    asset(intro["poster"], intro["poster_sha256"])
    asset(intro["chapters_src"], intro.get("chapters_sha256"))
    asset(intro.get("teaser", TEASER), intro.get("teaser_sha256"))

    site_rel = "docs/assets/data/site-data.json"
    selection_rel = "docs/assets/data/media-selection.json"
    site, selection = read(root / site_rel), read(root / selection_rel)
    old_intro = dict(site["intro"])
    preserved_site = {k: v for k, v in site.items() if k not in {"intro", "videos"}}
    preserved_selection = {k: v for k, v in selection.items()
                           if k not in {"intro", "videos", "selection", "archived_videos"}}
    results_path = root / "docs/assets/data/results.csv"
    results_sha = sha(results_path)
    site["videos"] = gallery
    site["intro"] = {
        "src": intro["src"], "poster": intro["poster"], "title": intro["title"],
        "duration": duration, "sha256": intro["sha256"], "chapters": intro["chapters_src"],
    }
    # Retire old gallery entries without breaking published player links. Archived
    # entries resolve in the player but do not appear among recommended examples.
    archived = {v["id"]: v for v in selection.get("archived_videos", [])}
    archived.update({v["id"]: v for v in selection["videos"] if v["id"] not in ids})
    for current_id in ids:
        archived.pop(current_id, None)
    selection["archived_videos"] = list(archived.values())
    selection["videos"] = gallery
    selection["intro"] = dict(intro)
    selection["selection"] = (
        "Selected illustrative closed-loop rollouts, chosen for scene diversity, route "
        "completion and HD-Score, with duration considered in the visual review. "
        "Difficulty and scores are reported per example; these examples are not a random "
        "or population-representative sample. Original experiment outputs are unchanged."
    )
    payloads[site_rel] = encode(site)
    payloads[selection_rel] = encode(selection)
    payloads["docs/assets/data/intro-edit.json"] = encode(intro)

    index = (root / "docs/index.html").read_text(encoding="utf-8")
    original_index = index
    for key in ("src", "poster"):
        if old_intro[key] not in index:
            raise ValueError(f"Index missing old introduction {key}")
        index = index.replace(old_intro[key], intro[key])
    index = index.replace(old_intro["chapters"], intro["chapters_src"])
    index = index.replace("The selected hard/extreme videos", "The selected videos")
    index = replace_once(index, duration_label(old_intro["duration"]), duration_label(duration), "index duration")
    hero_match = re.search(r'<video\b[^>]*\bid="hero-video"[^>]*>', index)
    if not hero_match:
        raise ValueError("No hero-video element")
    hero = re.sub(r'\s+(?:muted|autoplay)(?:=(?:"[^"]*"|\'[^\']*\'))?', "", hero_match.group())
    hero = hero.replace("HUGSIM hard and extreme rollouts", "selected HUGSIM closed-loop rollouts")
    if " controls" not in hero:
        raise ValueError("Hero video must retain native playback/audio controls")
    index = index[:hero_match.start()] + hero + index[hero_match.end():]
    payloads["docs/index.html"] = index.encode("utf-8")

    readme = (root / "README.md").read_text(encoding="utf-8")
    original_readme = readme
    readme = replace_once(readme, "docs/assets/images/intro-logo-teaser.gif",
                          "docs/" + intro.get("teaser", TEASER), "README introduction teaser")
    readme = replace_once(readme, duration_label(old_intro["duration"]), duration_label(duration), "README duration")
    readme = readme.replace("Play the DriveTTO project video with its animated logo opening",
                            "Play the DriveTTO introduction with original music")
    start_heading = "### 🛣️ HUGSIM closed-loop rollouts"
    end_heading = "### 🧭 NAVSIM planning animations"
    gallery_start, gallery_end = readme.index(start_heading), readme.index(end_heading)
    rows = [start_heading, "", '<table align="center">', "<tbody>"]
    for i, v in enumerate(gallery):
        if i % 3 == 0:
            rows.append("<tr>")
        link = BASE + "player.html?v=" + quote(v["id"], safe="")
        label = (f"{v['dataset']} · {v['difficulty']} · {duration_label(v['duration'])}"
                 f" · RC {float(v['rc']):.1f} · HD {float(v['hd']):.1f}")
        rows.append(
            '<td align="center"><a href="' + html.escape(link, quote=True) + '"><img src="docs/'
            + html.escape(v["poster"], quote=True) + '" width="320" alt="'
            + html.escape(v["title"], quote=True) + '"></a><p align="left"><strong>'
            + html.escape(v["title"]) + '</strong><br><em>' + html.escape(label) + "</em></p></td>"
        )
        if i % 3 == 2 or i == len(gallery) - 1:
            rows.append("</tr>")
    rows += ["</tbody>", "</table>", "", ""]
    readme = readme[:gallery_start] + "\n".join(rows) + readme[gallery_end:]
    if readme[readme.index(end_heading):] != original_readme[original_readme.index(end_heading):]:
        raise ValueError("NAVSIM README layout changed")
    if readme[:readme.index("## 🎬 Visualizations")] != original_readme[:original_readme.index("## 🎬 Visualizations")]:
        raise ValueError("README title or introduction changed")
    payloads["README.md"] = readme.encode("utf-8")

    app = (root / "docs/app.js").read_text(encoding="utf-8")
    app = replace_once(app, "heroVideo.muted = true;", "heroVideo.muted = false;", "intro audio setting")
    payloads["docs/app.js"] = app.encode("utf-8")
    player = (root / "docs/player.js").read_text(encoding="utf-8")
    player = replace_once(player, "    videoEl.src = item.src;", """    videoEl.src = item.src;
    if (item.id === "intro") {
      videoEl.removeAttribute("muted");
      videoEl.removeAttribute("autoplay");
      videoEl.defaultMuted = false;
      videoEl.muted = false;
      videoEl.controls = true;
    }""", "player introduction audio")
    player = replace_once(player, "    return items;", """    (d.archived_videos || []).forEach(function (v) {
      push(v.id, v.title || v.id, v.src, v.poster,
        ["HUGSIM · " + (v.dataset || ""), (v.difficulty || "").toUpperCase(),
         "RC " + Number(v.rc).toFixed(1), "HD " + Number(v.hd).toFixed(1)], v.description);
      items[items.length - 1].archived = true;
    });
    return items;""", "archived video resolver")
    player = player.replace("// related: other clips in the same group of up to 8", "// Other current videos; archived examples remain accessible by their old links.")
    player = replace_once(player, "return c.id !== item.id;", "return c.id !== item.id && !c.archived;", "related gallery filter")
    player = replace_once(player, "others.slice(0, 8).forEach", "others.forEach", "related gallery limit")
    payloads["docs/player.js"] = player.encode("utf-8")

    # All inputs, rendering and protected-content assertions complete before writes.
    if preserved_site != {k: v for k, v in site.items() if k not in {"intro", "videos"}}:
        raise ValueError("Protected benchmark or qualitative data changed")
    if preserved_selection != {k: v for k, v in selection.items()
                               if k not in {"intro", "videos", "selection", "archived_videos"}}:
        raise ValueError("Protected source or NAVSIM media metadata changed")
    backup = stage / "before"
    changed = []
    before_hashes = {}

    def save(rel, content):
        destination = root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        previous = sha(destination) if destination.exists() else None
        wanted = sha(content) if isinstance(content, Path) else hashlib.sha256(content).hexdigest()
        if previous == wanted:
            return
        if destination.exists():
            saved = backup / rel
            saved.parent.mkdir(parents=True, exist_ok=True)
            if saved.exists() and sha(saved) != previous:
                raise ValueError(f"Backup already has different contents: {rel}")
            if not saved.exists():
                shutil.copy2(destination, saved)
        before_hashes[rel] = previous
        if isinstance(content, Path):
            shutil.copy2(content, destination)
        else:
            destination.write_bytes(content)
        if sha(destination) != wanted:
            raise ValueError(f"Written file failed verification: {rel}")
        changed.append(rel)

    # Check every prospective backup before writing the first destination.
    for rel in list(payloads) + ["WEBSITE_MANIFEST.json"]:
        destination, saved = root / rel, backup / rel
        if saved.exists() and destination.exists() and sha(saved) != sha(destination):
            raise ValueError(f"Refusing to overwrite a prior publication: {rel}")
    for rel, content in payloads.items():
        save(rel, content)
    manifest_path = root / "WEBSITE_MANIFEST.json"
    old_manifest = read(manifest_path)
    paths = {p.relative_to(root).as_posix() for p in docs.rglob("*") if p.is_file()}
    paths.update(v["path"] for v in old_manifest["files"] if (root / v["path"]).is_file())
    paths.update(rel for rel in ("README.md", "WEBSITE.md", ".github/workflows/pages.yml",
                                 "tools/publish_recut_gallery.py", "tools/render_recut_20261030.py",
                                 "tools/generate_recut_music.py", "tools/polish_recut_chapters.py",
                                 "tools/extend_recut_high_scores.py") if (root / rel).is_file())
    paths.discard("WEBSITE_MANIFEST.json")
    manifest = {"files": [{"path": rel, "bytes": (root / rel).stat().st_size,
                            "sha256": sha(root / rel)} for rel in sorted(paths)]}
    save("WEBSITE_MANIFEST.json", encode(manifest))
    if sha(results_path) != results_sha:
        raise ValueError("results.csv changed")
    subprocess.run(["git", "diff", "--check"], cwd=root, check=True)
    publication = {
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root), "stage": str(stage), "changed_files": changed,
        "before_sha256": before_hashes,
        "files": [{"path": rel, "sha256": sha(root / rel), "bytes": (root / rel).stat().st_size}
                  for rel in changed],
        "gallery_count": len(gallery), "archived_gallery_count": len(archived),
        "intro_duration_seconds": duration, "media": source_assets,
        "results_csv_sha256": results_sha, "results_csv_unchanged": True,
        "benchmark_tables_unchanged": True, "navsim_layout_and_metadata_unchanged": True,
        "readme_title_and_overview_unchanged": True,
        "intro_audio_enabled_on_user_play": True, "autoplay_added": False,
        "git_committed": False, "git_pushed": False,
    }
    (stage / "PUBLICATION_PREPARED.json").write_bytes(encode(publication))
    print(json.dumps(publication, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
