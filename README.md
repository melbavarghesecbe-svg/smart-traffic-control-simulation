# Smart Traffic Control Simulation

An interactive Python simulation of a 4-way urban intersection with adaptive traffic signals, emergency priority, and real-time analytics.

## Overview

This project models realistic intersection behavior and compares two control strategies:

- Fixed-time traffic signaling.
- Adaptive signaling based on live congestion and waiting-time pressure.

It also includes emergency-vehicle priority behavior, pedestrian overrides, and weather/time driving effects (rain and night mode).

## Why This Project Matters

Urban traffic management has real constraints that static signals do not handle well. This simulation helps explore practical control logic in a safe, low-cost environment.

- Reduces trial-and-error on real roads by testing logic in simulation first.
- Demonstrates emergency-aware traffic behavior for faster critical response.
- Captures measurable metrics for data-driven decisions.
- Models safety-relevant conditions like rain and night driving.

## Key Features

### Traffic Signal Intelligence

- Fixed signal timing mode.
- Adaptive signal timing mode.
- Adaptive scoring based on congestion and average waiting time.
- Pedestrian crossing override.
- Emergency override with approach-based signal priority.

### Vehicle Behavior

- Multi-direction lane movement at a 4-way junction.
- Car-following logic with safe gap control.
- Acceleration and deceleration behavior.
- Reaction delay near stop lines.
- Safe lane-change and simple overtake behavior.

### Emergency Handling

- Dedicated emergency vehicle in the simulation.
- Signal preemption to prioritize the emergency direction.
- Nearby vehicles attempt to clear lane and reduce speed.
- Cross-traffic slows/stops to improve emergency passage.

### Environment Effects

- Rain mode:
	- Reduced speed.
	- Increased following distance.
	- Slower acceleration and reaction.
- Night mode:
	- Mild speed reduction.
	- Increased reaction delay.
	- Additional safety spacing.

### Analytics and Export

- Live HUD with signal state, congestion, and wait metrics.
- Debug panel for decision scores.
- Time-series metric collection.
- CSV export:
	- simulation_metrics.csv
	- simulation_summary.csv
- Post-simulation charting with matplotlib.

## Tech Stack

- Python 3
- Pygame (real-time simulation and rendering)
- Matplotlib (post-run analytics charts)
- csv (metric export)
- Standard library modules: random, time, sys

## Project Structure

- main.py: simulation loop, controls, rendering, analytics export.
- signal.py: traffic signal state machine and adaptive decision logic.
- vehicle.py: vehicle dynamics, yielding, lane logic, and environment effects.

## Controls

- Space: Pause or resume simulation.
- P: Toggle pedestrian crossing override.
- R: Toggle rain mode.
- N: Toggle day/night mode.
- D: Toggle debug panel.

## Run Locally

1. Install dependencies:

```bash
pip install pygame matplotlib
```

2. Run simulation:

```bash
python main.py
```

3. Optional comparison mode (adaptive vs fixed):

```bash
python main.py --compare --duration=60
```

## Outputs

After a run, the project can export:

- simulation_metrics.csv (time-based detailed metrics)
- simulation_summary.csv (overall summary metrics)

## Demo

### Screenshots

Add image files in the assets folder and reference them like this:

![Simulation Overview](assets/screenshot-overview.png)
![Emergency Priority](assets/screenshot-emergency.png)

### Video

GitHub README pages display images and GIFs best. For full video, use one of these approaches:

- Upload demo.mp4 to YouTube and add a link:
	[Watch Demo Video](https://www.youtube.com/)
- Add a short GIF preview in assets and embed it:
	![Demo GIF](assets/demo.gif)

## Future Improvements

- Multi-intersection network simulation.
- Better route-level traffic generation.
- Machine-learning-based signal optimization.
- Integration with real-world traffic datasets.

## Author

Melba Varghese

GitHub: https://github.com/melbavarghesecbe-svg
