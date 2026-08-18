# Results

Cost model: volume factor 1.000 (assumed 200 total reviews). Positive class is "not genuine". Routed cases are excluded from the confusion matrix and reported as human-review rate.

## Held-out test set (40 cases)

| System | TP | FP | TN | FN | Routed | Precision | Recall | Recall (routed in denom.) | Human review | Total cost | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline_keyword | 11 | 6 | 14 | 9 | 0 | 0.647 | 0.550 | 0.550 | 0.000 | 68.000 | - |
| expected_cost | 13 | 1 | 13 | 2 | 11 | 0.929 | 0.867 | 0.650 | 0.275 | 31.000 | 0.145 |
| fixed_band | 14 | 1 | 15 | 4 | 6 | 0.933 | 0.778 | 0.700 | 0.150 | 42.000 | 0.145 |

**baseline_keyword** emits no probability, so it cannot be calibrated. That is a finding, not an omission.

**expected_cost — reliability**

| Belief bin | n | Mean predicted | Observed fake rate |
|---|---|---|---|
| [0.0,0.2) | 15 | 0.025 | 0.133 |
| [0.2,0.4) | 4 | 0.329 | 0.500 |
| [0.4,0.6) | 1 | 0.592 | 1.000 |
| [0.6,0.8) | 5 | 0.696 | 0.200 |
| [0.8,1.0) | 15 | 0.972 | 0.933 |

Expected calibration error: 0.145

**fixed_band — reliability**

| Belief bin | n | Mean predicted | Observed fake rate |
|---|---|---|---|
| [0.0,0.2) | 15 | 0.025 | 0.133 |
| [0.2,0.4) | 4 | 0.329 | 0.500 |
| [0.4,0.6) | 1 | 0.592 | 1.000 |
| [0.6,0.8) | 5 | 0.696 | 0.200 |
| [0.8,1.0) | 15 | 0.972 | 0.933 |

Expected calibration error: 0.145

## Supplementary probe set (12 cases)

| System | TP | FP | TN | FN | Routed | Precision | Recall | Recall (routed in denom.) | Human review | Total cost | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline_keyword | 6 | 3 | 2 | 1 | 0 | 0.667 | 0.857 | 0.857 | 0.000 | 14.500 | - |
| expected_cost | 2 | 0 | 5 | 4 | 1 | 1.000 | 0.333 | 0.286 | 0.083 | 15.000 | 0.210 |
| fixed_band | 2 | 0 | 5 | 4 | 1 | 1.000 | 0.333 | 0.286 | 0.083 | 17.000 | 0.210 |

**baseline_keyword** emits no probability, so it cannot be calibrated. That is a finding, not an omission.

**expected_cost — reliability**

| Belief bin | n | Mean predicted | Observed fake rate |
|---|---|---|---|
| [0.0,0.2) | 6 | 0.162 | 0.500 |
| [0.2,0.4) | 3 | 0.302 | 0.333 |
| [0.4,0.6) | 0 | - | - |
| [0.6,0.8) | 1 | 0.622 | 1.000 |
| [0.8,1.0) | 2 | 0.990 | 1.000 |

Expected calibration error: 0.210

**fixed_band — reliability**

| Belief bin | n | Mean predicted | Observed fake rate |
|---|---|---|---|
| [0.0,0.2) | 6 | 0.162 | 0.500 |
| [0.2,0.4) | 3 | 0.302 | 0.333 |
| [0.4,0.6) | 0 | - | - |
| [0.6,0.8) | 1 | 0.622 | 1.000 |
| [0.8,1.0) | 2 | 0.990 | 1.000 |

Expected calibration error: 0.210
