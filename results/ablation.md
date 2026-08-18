# Ablation and base-rate sensitivity

Both checks were added after the AI reviews in `review-record.md`.

## Do the six hand-designed features contribute anything?

| Channels | Policy | TP | FP | TN | FN | Routed | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| features + lexical | fixed_band | 14 | 1 | 15 | 4 | 6 | 0.933 | 0.778 |
| features + lexical | expected_cost | 13 | 1 | 13 | 2 | 11 | 0.929 | 0.867 |
| lexical only | fixed_band | 13 | 2 | 15 | 4 | 6 | 0.867 | 0.765 |
| lexical only | expected_cost | 13 | 1 | 14 | 2 | 10 | 0.929 | 0.867 |
| features only | fixed_band | 0 | 0 | 13 | 5 | 22 | - | 0.000 |
| features only | expected_cost | 0 | 0 | 0 | 0 | 40 | - | - |

**Reading (computed from the table above, not asserted).** With the feature terms genuinely omitted, the lexical channel alone reaches recall 0.765 (fixed band) and 0.867 (expected cost), against 0.778 and 0.867 for the full system. Features alone reach recall 0.000. Read the deltas rather than any sentence written in advance.


## How far do the headline numbers travel?

| Prior P(fake) | Policy | TP | FP | TN | FN | Routed | Precision | Recall |
|---|---|---|---|---|---|---|---|---|
| 0.5 | fixed_band | 14 | 1 | 15 | 4 | 6 | 0.933 | 0.778 |
| 0.5 | expected_cost | 13 | 1 | 13 | 2 | 11 | 0.929 | 0.867 |
| 0.3 | fixed_band | 13 | 1 | 17 | 6 | 3 | 0.929 | 0.684 |
| 0.3 | expected_cost | 11 | 1 | 15 | 3 | 10 | 0.917 | 0.786 |
| 0.1 | fixed_band | 7 | 1 | 19 | 7 | 6 | 0.875 | 0.500 |
| 0.1 | expected_cost | 3 | 0 | 17 | 5 | 15 | 1.000 | 0.375 |
| 0.05 | fixed_band | 2 | 0 | 19 | 8 | 11 | 1.000 | 0.200 |
| 0.05 | expected_cost | 1 | 0 | 19 | 6 | 14 | 1.000 | 0.143 |

**Reading (computed).** Moving the prior from 0.5 to 0.1 changes fixed-band recall 0.778 -> 0.500 and expected-cost recall 0.867 -> 0.375. The headline figures are conditional on a 50% base rate that no deployment would have.

## How far does the cost model travel?

`total_reviews` sets the volume factor. Only 200 was ever reported.

| total_reviews | volume factor | Policy | permit | flag | route | hide | genuine hidden |
|---|---|---|---|---|---|---|---|
| 200 | 1.00 | fixed_band | 19 | 15 | 6 | 0 | 0 |
| 200 | 1.00 | expected_cost | 15 | 0 | 11 | 14 | 1 |
| 1000 | 0.20 | fixed_band | 19 | 15 | 6 | 0 | 0 |
| 1000 | 0.20 | expected_cost | 13 | 7 | 0 | 20 | 5 |
| 5000 | 0.04 | fixed_band | 19 | 15 | 6 | 0 | 0 |
| 5000 | 0.04 | expected_cost | 10 | 5 | 0 | 25 | 7 |
| 20000 | 0.01 | fixed_band | 19 | 15 | 6 | 0 | 0 |
| 20000 | 0.01 | expected_cost | 0 | 13 | 0 | 27 | 8 |

**Reading (computed).** The volume factor divides the cost of acting wrongly against a genuine review but not the cost of routing, so as a seller's review count rises, hiding gets cheaper while human review stays at 1.0. The reported configuration (200 reviews) is the most conservative point in this range, and that was not previously stated.
