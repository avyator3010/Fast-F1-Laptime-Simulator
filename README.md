## FastF1 Lap-Time Simulator 🏎️

A Python-based quasi-steady-state (QSS) Formula 1 lap-time simulator developed to investigate vehicle dynamics and performance around Silverstone.

## Methodology
- Reconstructed circuit geometry using FastF1 positional telemetry and cubic splines.
- Modelled tyre grip with load sensitivity and aerodynamic downforce.
- Implemented a forward–backward speed solver for braking, cornering and acceleration.
- Compared simulated performance against Max Verstappen's 2025 British Grand Prix qualifying lap.

## Results

| Metric | Lap time |
|---|---:|
| Simulated | 84.295 s |
| Reference | 84.892 s |
| Difference | 0.597 s (0.70%) |

The close overall lap time masks differences in corner-entry speeds and straight-line performance, highlighting the limitations of the simplified model.

## Technologies
Python · FastF1 · NumPy · SciPy · Matplotlib

## Report
See [`FastF1_Sim.pdf`](FastF1_Sim.pdf) for the full methodology, results and discussion.

## Limitations & Future Work
The model uses simplified tyre behaviour, constant effective power and a fixed racing line. Future improvements could include combined-slip tyre modelling and testing across additional circuits.
