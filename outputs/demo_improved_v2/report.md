# PX4 Offline Tuner Report

- Input: `sample_data\demo_log.csv`
- Output: `outputs\demo_improved_v2`

## Summary
- Roll best preset is 'aggressive' (quality=0.50, fit=0.72, score=53.0).
- Pitch best preset is 'aggressive' (quality=0.50, fit=0.71, score=52.3).
- Yaw best preset is 'aggressive' (quality=0.50, fit=0.70, score=52.0).

## Axis: roll

- Quality score: `0.50`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1550 s`
- Model gain: `0.487`
- Model time constant: `0.0461 s`
- Model dead time: `0.1950 s`
- Model fit score: `0.72`

### Diagnostics
- Setpoint excitation is weak; identification confidence will be limited.
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Estimated delay is large relative to plant time constant; robustness margin is limited.
- Model bias is noticeable; the recommendation engine will lean conservative.
- Model fit is acceptable for offline comparative tuning.

### Recommendations
- `conservative`: Kp=0.09706, Ki=0.71332, Kd=0.00662, risk=low
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=43.93, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.72, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.12479, Ki=0.9654, Kd=0.00852, risk=medium
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=48.67, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.72, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=0.16985, Ki=1.28899, Kd=0.01104, risk=high
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=52.95, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.72, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.

## Axis: pitch

- Quality score: `0.50`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1600 s`
- Model gain: `0.474`
- Model time constant: `0.0461 s`
- Model dead time: `0.2000 s`
- Model fit score: `0.71`

### Diagnostics
- Setpoint excitation is weak; identification confidence will be limited.
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Estimated delay is large relative to plant time constant; robustness margin is limited.
- Model bias is noticeable; the recommendation engine will lean conservative.
- Model fit is acceptable for offline comparative tuning.

### Recommendations
- `conservative`: Kp=0.09737, Ki=0.70333, Kd=0.00682, risk=low
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=43.21, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.71, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.12518, Ki=0.95188, Kd=0.00876, risk=medium
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=47.93, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.71, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=0.17039, Ki=1.27093, Kd=0.01136, risk=high
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=52.27, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.71, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.

## Axis: yaw

- Quality score: `0.50`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1650 s`
- Model gain: `0.436`
- Model time constant: `0.0461 s`
- Model dead time: `0.2000 s`
- Model fit score: `0.70`

### Diagnostics
- Setpoint excitation is weak; identification confidence will be limited.
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Estimated delay is large relative to plant time constant; robustness margin is limited.
- Model bias is noticeable; the recommendation engine will lean conservative.
- Model fit is acceptable for offline comparative tuning.

### Recommendations
- `conservative`: Kp=0.10589, Ki=0.76492, Kd=0.00741, risk=low
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=43.03, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.70, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.13615, Ki=1.03523, Kd=0.00953, risk=medium
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=47.70, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.70, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=0.18531, Ki=1.38222, Kd=0.01235, risk=high
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=52.00, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.70, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.
