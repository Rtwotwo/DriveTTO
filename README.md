<h1 align="center">DriveTTO: Understanding Search and Selection in Test-Time Trajectory Optimization</h1>

<p align="center">
  <img src="https://img.shields.io/badge/arXiv-B31B1B?logo=arxiv&amp;logoColor=white" alt="arXiv" height="24">
  <a href="https://github.com/Rtwotwo/DriveTTO"><img src="https://img.shields.io/badge/GitHub-181717?logo=github&amp;logoColor=white" alt="GitHub repository" height="24"></a>
  <a href="https://rtwotwo.github.io/DriveTTO/"><img src="https://img.shields.io/badge/GitHub.io-2563EB?logo=githubpages&amp;logoColor=white" alt="GitHub Pages project website" height="24"></a>
</p>

## Overview

<p align="center"><a href="assets/overview.png"><img src="assets/overview.png" alt="DriveTTO overview" width="100%"></a></p>

**DriveTTO is a training-free framework for test-time trajectory optimization that connects structured search with reference-relative selection.** A driving planner may generate a good trajectory yet fail to select it. Adding more candidates therefore makes both trajectory quality and selection quality central to the value of search. DriveTTO explores alternatives around a retained complete plan and compares each proposed update with that reference, while keeping the driving models frozen throughout inference. Across the corresponding benchmark settings, DriveTTO achieves **95.5 PDMS** and **92.3 EPDMS** on NAVTEST, **57.1 EPDMS** on NAVHARD, and **54.5 route completion (RC)** with **40.1 HD-Score** on 345 HUGSIM scenarios. The single-scorer variant, **DriveTTO-S**, is also evaluated across six base planners against their native outputs and ToAD. [Full results](https://rtwotwo.github.io/DriveTTO/#results). The animation below illustrates how DriveTTO searches and selects around a retained complete plan at test time.

<p align="center">
  <video controls muted playsinline preload="metadata" poster="docs/assets/images/algorithm-poster.jpg" width="640">
    <source src="docs/assets/videos/drivetto-algorithm-animation.mp4" type="video/mp4">
  </video>
</p>

Concretely, endpoint feedback associates the predicted utility of a complete trajectory with its achieved terminal state, guiding further search through the planner's native path geometry. Geometric refinement, cross-model proposals and bounded control residuals produce alternative motions around the retained plan. Frozen scorers evaluate gains over the reference in a shared scoring context, and temporal fusion combines proposal and control trajectories along the prediction horizon. Each accepted update becomes the reference for later decisions. By separating the best trajectory available in a candidate pool from the trajectory actually returned, DriveTTO examines how candidate construction, filtering and ranking contribute to the final driving result.
