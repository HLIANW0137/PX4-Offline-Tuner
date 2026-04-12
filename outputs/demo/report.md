# PX4 Offline Tuner Report

- Input: `sample_data\demo_log.csv`
- Output: `outputs\demo`

## Summary
- Roll best preset is 'aggressive' (quality=0.50, fit=0.81).
- Pitch best preset is 'conservative' (quality=0.50, fit=0.11).
- Yaw best preset is 'aggressive' (quality=0.50, fit=0.60).

## Axis: roll

- Quality score: `0.50`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1550 s`
- Model gain: `0.646`
- Model time constant: `0.0200 s`
- Model dead time: `0.1550 s`
- Model fit score: `0.81`

### Diagnostics
- Setpoint excitation is weak; identification confidence will be limited.
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Model fit is acceptable for offline comparative tuning.

### Recommendations
- `conservative`: Kp=0.03995, Ki=0.45527, Kd=0.00217, risk=low
  - Simulated rise=infs, settle=infs, overshoot=0.00%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.81, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.05136, Ki=0.58535, Kd=0.00279, risk=medium
  - Simulated rise=infs, settle=infs, overshoot=0.00%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.81, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=0.06658, Ki=0.75879, Kd=0.00361, risk=high
  - Simulated rise=infs, settle=infs, overshoot=0.00%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.81, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.

## Axis: pitch

- Quality score: `0.50`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1600 s`
- Model gain: `0.620`
- Model time constant: `1.4500 s`
- Model dead time: `0.1600 s`
- Model fit score: `0.11`

### Diagnostics
- Setpoint excitation is weak; identification confidence will be limited.
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Model fit is modest; use conservative or balanced recommendations first.

### Recommendations
- `conservative`: Kp=2.92392, Ki=2.1234, Kd=0.16374, risk=low
  - Simulated rise=1.585s, settle=2.260s, overshoot=0.00%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.11, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=3.75933, Ki=2.73008, Kd=0.21052, risk=medium
  - Simulated rise=1.220s, settle=1.690s, overshoot=1.40%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.11, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=4.14222, Ki=3.1851, Kd=0.2729, risk=high
  - Simulated rise=1.075s, settle=1.420s, overshoot=2.82%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.11, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.
  - Aggressive preset was tempered because identification confidence is limited.

## Axis: yaw

- Quality score: `0.50`
- Dominant frequency: `0.53 Hz`
- Noise frequency: `0.53 Hz`
- Estimated bandwidth: `1.05 Hz`
- Estimated delay: `0.1650 s`
- Model gain: `0.601`
- Model time constant: `0.3000 s`
- Model dead time: `0.1650 s`
- Model fit score: `0.60`

### Diagnostics
- Setpoint excitation is weak; identification confidence will be limited.
- Tracking error is noisy; derivative recommendations should be treated carefully.
- Bandwidth looks low; the loop is likely too conservative.
- Tracking RMS error is elevated; consider more authority in the balanced preset.
- Estimated delay is meaningful; aggressive tuning may reduce robustness.
- Model fit is acceptable for offline comparative tuning.

### Recommendations
- `conservative`: Kp=0.60483, Ki=1.75695, Kd=0.03493, risk=low
  - Simulated rise=2.005s, settle=infs, overshoot=0.00%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 3.5.
  - Model fit score is 0.60, so the conservative preset emphasizes robustness.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `balanced`: Kp=0.77764, Ki=2.25893, Kd=0.04491, risk=medium
  - Simulated rise=1.505s, settle=2.450s, overshoot=0.00%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 2.5.
  - Model fit score is 0.60, so the balanced preset emphasizes balanced tracking.
  - Delay compensation reduced P and D slightly to preserve robustness.
- `aggressive`: Kp=1.00805, Ki=2.92825, Kd=0.05821, risk=high
  - Simulated rise=1.105s, settle=1.730s, overshoot=0.00%, stable=True
  - Derived from an IMC-style FOPDT tuning law with lambda factor 1.7.
  - Model fit score is 0.60, so the aggressive preset emphasizes response speed.
  - Delay compensation reduced P and D slightly to preserve robustness.
