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



## Visualizations

<p align="center">
  <video controls muted playsinline preload="none" poster="docs/assets/images/intro-poster.jpg" width="720">
    <source src="docs/assets/videos/drivetto-introduction.mp4" type="video/mp4">
  </video>
</p>

<p align="center"><em>1 min 54 s · Method · Planning · Closed-loop driving — <a href="https://rtwotwo.github.io/DriveTTO/#videos">open the full gallery</a></em></p>

### HUGSIM closed-loop rollouts

<table align="center">
<tbody>
<tr>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/nuscenes-scene-0166-hard_00.jpg" width="320"><source src="docs/assets/videos/nuscenes-scene-0166-hard_00.mp4" type="video/mp4"></video><br><strong>Through the city blocks</strong><br><em>nuScenes · hard · RC 100.0 · HD 100.0</em></td>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/waymo-166085257829_0_200-hard_00.jpg" width="320"><source src="docs/assets/videos/waymo-166085257829_0_200-hard_00.mp4" type="video/mp4"></video><br><strong>Between parked vehicles</strong><br><em>Waymo · hard · RC 100.0 · HD 97.2</em></td>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/pandaset-028-medium_00.jpg" width="320"><source src="docs/assets/videos/pandaset-028-medium_00.mp4" type="video/mp4"></video><br><strong>Following along a residential street</strong><br><em>PandaSet · medium · RC 100.0 · HD 92.9</em></td>
</tr>
<tr>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/kitti360-0000_8440_8640-easy_00.jpg" width="320"><source src="docs/assets/videos/kitti360-0000_8440_8640-easy_00.mp4" type="video/mp4"></video><br><strong>From curbside parking to a crossing</strong><br><em>KITTI-360 · easy · RC 95.9 · HD 92.1</em></td>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/nuscenes-scene-0167-extreme_01.jpg" width="320"><source src="docs/assets/videos/nuscenes-scene-0167-extreme_01.mp4" type="video/mp4"></video><br><strong>Across a broad intersection</strong><br><em>nuScenes · extreme · RC 100.0 · HD 98.0</em></td>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/waymo-322492347634_0_200-extreme_01.jpg" width="320"><source src="docs/assets/videos/waymo-322492347634_0_200-extreme_01.mp4" type="video/mp4"></video><br><strong>An uphill urban corridor</strong><br><em>Waymo · extreme · RC 100.0 · HD 95.4</em></td>
</tr>
</tbody>
</table>

### NAVSIM planning animations

<table align="center">
<tbody>
<tr>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/00c489998dd4555c-front.webp" width="360"><source src="docs/assets/videos/navsim-00c489998dd4555c.mp4" type="video/mp4"></video><br><strong>Urban bend</strong><br><em>PDMS 100 · 4 s prediction horizon</em></td>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/0114734fd69b598e-front.webp" width="360"><source src="docs/assets/videos/navsim-0114734fd69b598e.mp4" type="video/mp4"></video><br><strong>Narrow street</strong><br><em>PDMS 100 · 4 s prediction horizon</em></td>
</tr>
<tr>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/013ec5b715635a66-front.webp" width="360"><source src="docs/assets/videos/navsim-013ec5b715635a66.mp4" type="video/mp4"></video><br><strong>Junction</strong><br><em>PDMS 100 · 4 s prediction horizon</em></td>
<td align="center"><video controls muted playsinline preload="none" poster="docs/assets/images/003ead1914c051d7-front.webp" width="360"><source src="docs/assets/videos/navsim-003ead1914c051d7.mp4" type="video/mp4"></video><br><strong>Bridge curve</strong><br><em>PDMS 100 · 4 s prediction horizon</em></td>
</tr>
</tbody>
</table>
