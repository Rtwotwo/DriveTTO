<h1 align="center">DriveTTO: Test-Time Trajectory Optimization<br>via Endpoint Search and Temporal Fusion</h1>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/GitHub-Code%20Coming%20Soon-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub: code coming soon"></a>
  <a href="#"><img src="https://img.shields.io/badge/arXiv-Paper%20Coming%20Soon-B31B1B?style=flat-square" alt="arXiv: paper coming soon"></a>
</p>

## Overview

**Test-time search gives a frozen driving planner additional computation to improve its trajectory.** DriveTTO is a training-free framework that builds complete alternatives around a retained reference plan and lets frozen scorers govern replacement. Supported endpoint search, bounded control residuals, and branch fusion construct these alternatives; temporal fusion re-anchors the previous plan from its observed pose and re-scores it against current candidates. No training is required, and the framework transfers to off-the-shelf planners.

Whether search benefit reaches the returned plan depends on whether better candidates survive shortlisting, admission, and ranking. DriveTTO addresses this with two complementary mechanisms:

- **Candidate construction around the reference** supplies supported endpoint changes, bounded control residuals, geometric search, and cross-model proposals that a frozen scorer pool can fairly compare.
- **Relative scoring and replacement** compares each candidate with the reference in shared contexts so that replacement is governed by relative gains, exposing exactly where candidate quality is lost.

## Preliminary Results

DriveTTO consistently improves frozen planners without any training. With frozen ChainFlow and DrivoR models, it reports state-of-the-art results on NAVSIM navtest (95.5 PDMS / 92.3 EPDMS) and compares favorably in additional NAVSIM settings and benchmark-specific configurations. On HUGSIM closed-loop evaluation over 345 scenarios, the observed-command configuration reaches 54.5 route completion and 40.1 HD-Score, leading the reported comparison, with a fixed-straight variant also improving the base planner by 4.3 RC / 4.0 HD. A single-scorer version further improves six frozen planners, and the same models gain over native-candidate reranking and fixed interpolation on navtest. Full tables and details will be released with the paper.
