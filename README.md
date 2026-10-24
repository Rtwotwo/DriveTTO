# DriveTTO: Understanding Search and Selection in Test-Time Trajectory Optimization

<p align="left">
  <img src="https://img.shields.io/badge/arXiv-Coming_soon-B31B1B?logo=arxiv&amp;logoColor=white" alt="arXiv — coming soon" title="Paper link coming soon" height="24">
  <a href="https://github.com/Rtwotwo/DriveTTO"><img src="https://img.shields.io/badge/GitHub-181717?logo=github&amp;logoColor=white" alt="GitHub repository" height="24"></a>
  <a href="https://rtwotwo.github.io/DriveTTO/"><img src="https://img.shields.io/badge/GitHub.io-2563EB?logo=githubpages&amp;logoColor=white" alt="GitHub Pages project website" height="24"></a>
</p>

## Overview

**DriveTTO optimizes driving trajectories at test time without updating model weights.** It combines endpoint feedback, trajectory refinement and frozen-model scoring to search for better plans around a planner's output. The method studies how the trajectories found by search and the rule used to select among them shape the final driving performance.

<p align="center"><a href="assets/overview.png"><img src="assets/overview.png" alt="DriveTTO overview" width="100%"></a></p>

## Video

<p align="center"><a href="https://rtwotwo.github.io/DriveTTO/#algorithm"><img src="docs/assets/images/algorithm-teaser.gif" alt="DriveTTO algorithm animation" width="640"></a></p>

[Project video](https://rtwotwo.github.io/DriveTTO/#introduction) · [Algorithm animation](https://rtwotwo.github.io/DriveTTO/#algorithm)

## Results

### Main benchmarks

| Benchmark | Metric | DriveTTO |
|:---|:---|:---|
| NAVSIM-v1 NAVTEST | PDMS ↑ | **95.5** |
| NAVSIM-v2 NAVTEST | EPDMS ↑ | **92.3** |
| NAVSIM-v2 NAVHARD | EPDMS ↑ | **57.1** |
| HUGSIM | Route completion ↑ | **54.5** |
| HUGSIM | HD-Score ↑ | **40.1** |

### Transfer across six planners

DriveTTO-S is the single-scorer transfer variant.

**NAVTEST PDMS**

| Base planner | Native | ToAD K10 | DriveTTO-S | Δ vs. ToAD |
|:---|:---|:---|:---|:---|
| ZTRS | 87.1306 | 88.5780 | 91.0221 | +2.4441 |
| GTRS | 90.9300 | 92.1587 | 93.5195 | +1.3608 |
| Hydra-MDP | 90.8336 | 92.2803 | 93.4641 | +1.1838 |
| iPad | 91.7879 | 93.4141 | 94.2302 | +0.8161 |
| RAP-DINO | 93.8203 | 94.4600 | 94.5679 | +0.1079 |
| DrivoR | 94.5389 | 94.7202 | 94.8672 | +0.1470 |

**NAVHARD EPDMS**

| Base planner | Native | ToAD K5 | DriveTTO-S | Δ vs. ToAD |
|:---|:---|:---|:---|:---|
| ZTRS | 46.1690 | 49.6922 | 51.4893 | +1.7971 |
| GTRS | 43.8706 | 49.3151 | 49.4346 | +0.1195 |
| Hydra-MDP | 41.1733 | 48.0827 | 47.6296 | -0.4531 |
| iPad | 36.8378 | 50.6090 | 47.8166 | -2.7924 |
| RAP-DINO | 38.6198 | 45.7217 | 52.5532 | +6.8315 |
| DrivoR | 54.5616 | 55.6365 | 56.2260 | +0.5895 |

[Full results and evaluation details](https://rtwotwo.github.io/DriveTTO/#results) · [Download CSV](https://rtwotwo.github.io/DriveTTO/assets/data/results.csv)
