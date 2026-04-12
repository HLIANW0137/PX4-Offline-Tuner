# PX4 Offline Tuner Report

- Primary input: `sample_data\demo_log.csv`
- Input count: `2`
- Output: `outputs\multi_demo`

## Summary

## Input Logs
- `sample_data\demo_log.csv`
- `sample_data\demo_log_variant.csv`
- Roll best preset is 'aggressive' (quality=0.85, fit=0.72, score=53.5).
- Pitch best preset is 'aggressive' (quality=0.85, fit=0.71, score=54.6).
- Yaw best preset is 'aggressive' (quality=0.85, fit=0.70, score=54.3).

## Axis: roll

- Quality score: `0.85`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1600 s`
- Model gain: `0.478`
- Model time constant: `0.0530 s`
- Model dead time: `0.2000 s`
- Model fit score: `0.72`

### Diagnostics
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Joint analysis combines 2 logs for this axis.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Estimated delay is large relative to plant time constant; robustness margin is limited.
- Model bias is noticeable; the recommendation engine will lean conservative.
- Model fit is acceptable for offline comparative tuning.
- Cross-log consistency score is 0.99; lower values indicate more variation between flights.

### Recommendations
- `conservative`: Kp=0.11099, Ki=0.7656, Kd=0.00777, risk=low
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=44.63, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.72, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.1427, Ki=1.03616, Kd=0.00999, risk=medium
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=49.35, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.72, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=0.19423, Ki=1.38346, Kd=0.01295, risk=high
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=53.53, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.72, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.

## Axis: pitch

- Quality score: `0.85`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1600 s`
- Model gain: `0.465`
- Model time constant: `0.0609 s`
- Model dead time: `0.2000 s`
- Model fit score: `0.71`

### Diagnostics
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Joint analysis combines 2 logs for this axis.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Estimated delay is large relative to plant time constant; robustness margin is limited.
- Model bias is noticeable; the recommendation engine will lean conservative.
- Model fit is acceptable for offline comparative tuning.
- Cross-log consistency score is 0.99; lower values indicate more variation between flights.

### Recommendations
- `conservative`: Kp=0.13109, Ki=0.85978, Kd=0.00918, risk=low
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=45.95, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.71, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.16855, Ki=1.16361, Kd=0.0118, risk=medium
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=50.61, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.71, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=0.22941, Ki=1.55364, Kd=0.01529, risk=high
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=54.57, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.71, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.

## Axis: yaw

- Quality score: `0.85`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1600 s`
- Model gain: `0.427`
- Model time constant: `0.0609 s`
- Model dead time: `0.2000 s`
- Model fit score: `0.70`

### Diagnostics
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Joint analysis combines 2 logs for this axis.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Estimated delay is large relative to plant time constant; robustness margin is limited.
- Model bias is noticeable; the recommendation engine will lean conservative.
- Model fit is acceptable for offline comparative tuning.
- Cross-log consistency score is 0.99; lower values indicate more variation between flights.

### Recommendations
- `conservative`: Kp=0.14263, Ki=0.93545, Kd=0.00998, risk=low
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=45.73, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.70, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.18338, Ki=1.26603, Kd=0.01284, risk=medium
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=50.35, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.70, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=0.2496, Ki=1.69038, Kd=0.01664, risk=high
  - Simulated rise=2.500s, settle=2.500s, overshoot=0.00%, score=54.26, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.70, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.
