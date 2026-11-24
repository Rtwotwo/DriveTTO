# DriveTTO project page

The buildless static website lives in `docs/`. Open it through an HTTP server:

```sh
python3 tools/serve_site.py --port 8765 --bind 127.0.0.1 --directory docs
```

## Publish on GitHub Pages

In this repository's **Settings → Pages → Build and deployment**, choose **GitHub Actions**. The included workflow publishes `docs/` on pushes to `main` or manual workflow dispatch.

Expected site URL: `https://rtwotwo.github.io/DriveTTO/`.

## Editing

- `docs/index.html`: page content and benchmark scope notes.
- `docs/styles.css`: responsive page layout.
- `docs/app.js`: video selection, result tabs, image preview.
- `docs/assets/data/site-data.json`: scene captions, media paths, tables.
- `docs/assets/data/results.csv`: downloadable numeric results.
- `docs/assets/data/media-selection.json`: selected media and source hashes, without private server paths.

The introductory video, method animation and scene clips are served locally. README and homepage paper buttons link to [arXiv:2611.29205](https://arxiv.org/abs/2611.29205). The downloadable citation is in docs/assets/drivetto.bib. The teaser and method overview are rendered from the paper.

The five headline values and other-method comparison tables are transcribed from the manuscript. The controlled three-seed experiment and the two six-planner transfer tables are labeled separately. `docs/assets/data/intro-edit.json` and `media-selection.json` record selected scenes and media hashes without private server paths.

The tables include all five PDMS components, all nine EPDMS components (separate S1/S2 rows for NAVHARD), and Easy/Medium/Hard/Extreme RC and HD-Score. HUGSIM overall averages cover all scenarios and are not calculated as the unweighted mean of the displayed difficulty averages. Component values are also included in the results CSV.

Website source is deployed at `/data/xinyao/release/DriveTTO`. The local preview server binds only to loopback; use SSH forwarding to preview it remotely. The GitHub Pages workflow is the public deployment route.

NAVTEST full-strategy, NAVHARD full57, HUGSIM command-v4, and R7 endpoint_post transfer are separate experimental settings. Their labels and interpretation notes must remain attached to their results.


The active introduction is 6:36 (2026-10-31). Its 2:48 method segment is a continuous NAV1 Full schematic linking endpoint utility feedback, two-planner refinement, matched-time fusion and vehicle-footprint close-ups. The selected HUGSIM and NAVSIM examples, their scores, and the qualitative image layouts are unchanged. Earlier media remain at their original URLs.
