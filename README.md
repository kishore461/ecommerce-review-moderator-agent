# E-commerce Review Moderation Agent

A cost-sensitive probabilistic agent that decides what to do with a newly
submitted customer review when it cannot tell whether the review is genuine.

> The agent observes a newly submitted customer review text and star rating.
> It must select permit, warn, hide, or report because whether the post is a
> genuine customer experience versus a paid spam or competitor fake review is
> not known.

Everything the agent does is driven by two observations only: **the review text
and the star rating**. No account age, no purchase history, no IP address, no
photos, no reviewer history. That constraint is the point of the project, and
it is enforced in code — `ModerationAgent.observe()` takes `(text, rating)` and
nothing else.

---

## Reproducing the experiment

Requires Python 3.11+. No third-party packages, no network access, no API keys.

```bash
# 1. Place the dataset
#    Fake Reviews Dataset (Salminen et al.), from Kaggle
#    -> data/fake reviews dataset.csv

# 2. Build the splits (deterministic, seed 20260817)
python experiments/build_testset.py

# 3. Run the baseline and both agent policies
python experiments/run_experiment.py

# 4. Score everything
python experiments/evaluate.py
```

Every step is seeded and deterministic. Running the three commands against the
same source download reproduces every number in `results/` exactly. The source
file is not pinned by checksum - see limitation 16.

### What each step writes

| Step | Output |
|---|---|
| `build_testset.py` | `data/fit_set.csv`, `data/test_set.csv`, `data/probe_set.csv` |
| `run_experiment.py` | `results/predictions_test.csv`, `results/predictions_probe.csv`, `results/likelihoods.json`, `results/lexical_top_words.md`, `results/run_manifest.json` |
| `experiments/evaluate.py` | `results/metrics.json`, `results/metrics.md`, `results/failures.md` |

---

## The agent

| Part | Implementation |
|---|---|
| **Input** | Review text + star rating (`src/features.py`) |
| **Hidden state** | `genuine`, `fake`, `solicited` (`src/agent.py: State`) |
| **Belief** | Posterior over those states, from six interpretable features plus a clipped lexical channel |
| **Action** | `permit`, `flag_with_explanation`, `route_to_human`, `hide` |
| **Cost** | Asymmetric, scaled by the business's total review volume (`CostModel`) |
| **Policy** | `FixedBandPolicy` (A) and `ExpectedCostPolicy` (B) |
| **Feedback** | `FeedbackLog` — records outcomes **only** for routed cases |

**Human reasoning function:** identify uncertainty, and send a high-cost
decision to a human rather than guessing. Both policies can decline to decide.
That is the only human faculty imitated here.

### The two policies

- **A — fixed bands.** Act above 85% belief, route 50–84% to a human queue,
  permit below 50%. The 85% came from a practitioner in r/trustandsafetypros.
  Its high-confidence action is `flag_with_explanation`, never `hide`, because a
  seller in r/Amazonsellercentral objected to autonomous hiding.
- **B — expected cost.** Choose the action minimising expected cost under the
  belief. No threshold anywhere; the effective threshold falls out of the cost
  matrix and the review volume. This policy *is* allowed to select `hide`.

The comparison is therefore a direct test of the design change made after the
r/Amazonsellercentral discussion.

### Baseline

`src/baseline.py` — a flat keyword rule with no belief, no cost model, and no
option to defer. Its threshold is tuned on the fit split, so it gets a fair run.
It exists to test a specific claim from r/learnmachinelearning: that
LLM-generated keyword lists inflate false positives.

---

## Results summary

Held-out test set, 40 cases, 20 genuine and 20 fake.

| System | Precision | Recall | Recall (routed in denom.) | FP | FN | Human review | Total cost | ECE |
|---|---|---|---|---|---|---|---|---|
| baseline_keyword | 0.647 | 0.550 | 0.550 | 6 | 9 | 0% | 68.0 | n/a |
| fixed_band (A) | 0.933 | 0.778 | **0.700** | 1 | 4 | 15% | 42.0 | 0.145 |
| expected_cost (B) | 0.929 | 0.867 | **0.650** | 1 | 2 | 27.5% | 31.0 | 0.145 |

**Read the fourth column, not the third.** The confusion matrix excludes routed
cases, but the baseline cannot route, so a policy is rewarded for declining while
the baseline is not. Counting routed cases as "not acted on" is the like-for-like
comparison — and under it **Policy A is more accurate than Policy B**, which
reverses the ranking the third column suggests. B routes five fakes it could not
classify; A routes two.

**The cost comparison is circular and should not be read as a result.** Policy B
selects the action minimising expected cost under a given cost model, and is then
scored with that same cost model. "B has lower total cost" is a property of
argmin, not a finding.

Both agent policies beat the baseline on the held-out set. **They do not beat it
everywhere** — on the 12-case probe set the baseline has higher recall (0.857 vs
0.333) and lower total cost. The probe set is designed to attack the agent's
assumptions, and it succeeds.

**The agent is not well calibrated.** ECE 0.145. The 0.6–0.8 belief band predicts
a mean of 0.696 against an observed 0.200 — but that bin holds five cases, so the
figure is indicative, not established. Bin counts are printed beside every
reliability table for this reason.

**The six hand-designed features contribute almost nothing measurable.** With the
feature terms genuinely omitted, the lexical channel alone reaches recall 0.765
(A) and 0.867 (B), against 0.778 and 0.867 for the full system — a difference of
one case on A and zero on B. Features alone decide nothing at all: recall 0.000,
because the belief never leaves the deferral band. An earlier version of this
README claimed the features raised recall from 0.632 to 0.778; that was an
artefact of a bug in the ablation, corrected after review 4. See
`results/ablation.md` and `review-record.md`.

Full tables: `results/metrics.md`. Failure analysis: `results/failures.md`.
Ablation and sensitivity: `results/ablation.md`.

---

## Limitations

These are material, and they qualify every number above.

1. **The dataset's labels are not the project's hidden states.** The Kaggle set
   labels rows `CG` (computer-generated) and `OR` (original human) — machine
   versus human authorship. The problem statement is about a *paid human* writing
   a fake. The experiment tests one corner of `fake` and says nothing about paid
   human fakes.
2. **Near-duplicate leakage into the fit split, on one class only.** The split
   de-duplicates on exact string equality, but the machine-generated rows repeat
   near-verbatim spans. At token-Jaccard > 0.30, 11 of 20 test fakes have a
   near-neighbour in the fit set against 0 of 20 genuine. The leakage lands on
   the positive class, so it inflates recall specifically. "Held out" is not
   fully earned.
3. **The `solicited` state is structurally undetectable.** Its likelihoods are
   copied from `genuine` for five of six features and it is assigned a lexical
   LLR of exactly zero, so `P(solicited)/P(genuine)` is bounded above by 0.402
   for any text whatsoever. It is not inferred from evidence; it is a fixed
   multiple of its prior. Where the decision record says the belief "moved into"
   this state, the prior put it there.
4. **60% of beliefs are pinned by a constant.** Raw lexical LLRs on the test set
   span roughly −79 to +82, and 24 of 40 cases saturate the ±4.0 clip exactly.
   For those the belief is a step function of the LLR's sign. `LLR_CLIP` is the
   most influential parameter in the system and the reported ECE is largely set
   by it. Consequently the 0.85 threshold is barely load-bearing: 0.80 and 0.85
   produce identical decisions on this set.
5. **Evidence is double-counted.** The lexical channel and the six features read
   the same text and are multiplied as if conditionally independent. The unigram
   model contains the very words the features count. This is the likely cause of
   the overconfidence in (4) and it is not fixed.
6. **Policy B can never flag.** Given this cost matrix, `flag` is weakly
   dominated by `route` for every belief, so B's only enforcement action is
   autonomous hiding — 14 of 40 cases, one of them genuine. The A-versus-B
   comparison therefore confounds two changes at once: threshold-versus-cost, and
   flag-only-versus-hide-only.
7. **The cost model was reported at its most conservative point.** Only
   `total_reviews = 200` was ever run. Sweeping it (see `results/ablation.md`)
   shows that at 20,000 reviews Policy B routes nothing at all and hides 27 of
   40, because hiding becomes cheaper than a human's time. The stated human
   reasoning function switches off exactly for the largest sellers.
8. **Human review is modelled as free, instant and infallible**, at a flat cost
   of 1.0 under every state, and the experiment feeds ground truth in as the
   human verdict — so the printed "overturn rate" is a relabelled ground-truth
   count, not feedback.
9. **The customer who wrote the review is not in the cost model.** They lose
   their words with no notification and no appeal, and the volume factor scales
   that harm by the *seller's* review count.
10. **`p_not_genuine` pools `fake` with `solicited`** despite very different
    costs, so Policy A will act identically on a suspected paid faker and on a
    real customer who happens to know the owner.
11. **The lexical channel partly memorises product vocabulary** — top
    discriminative unigrams include `schlage`, `taurus`, `sneaker`.
12. **Specificity is not adversarially robust.** A Yelp reviewer pointed out that
    a motivated faker lifts detail from the page they are attacking.
13. **Feedback is one-sided.** Permitted reviews generate no correction signal.
14. **The probe set is synthetic and author-written**, which is why it is
    reported separately and never mixed into the 40.
15. **Sarcasm is unsolved**, and the polarity-mismatch feature carries almost no
    signal (log ratio ≈ 0.05).
16. **The source dataset is not pinned.** No checksum or row count is recorded,
    so "reproduces every number exactly" holds only against the same download.

---

## Repository layout

```
src/
  features.py    six interpretable features, text + rating only
  lexical.py     clipped unigram Naive Bayes channel
  prompts.py     marker word lists, with provenance
  agent.py       states, belief, costs, policies, feedback
  baseline.py    keyword baseline
experiments/
  build_testset.py   deterministic splits + probe set
  run_experiment.py  runs baseline and both policies
  evaluate.py        metrics, calibration, failure analysis
data/            source dataset and generated splits
results/         predictions, metrics, failures, audit files
research-file.md      terms, sources, communities, AI errors
discussion-record.md  every public discussion and what it changed
```

---

## AI use

This code was written with AI assistance. The design decisions it implements —
the probability bands, flag-with-explanation instead of autonomous hide, the
volume-weighted cost matrix, the specificity signal and its fragility, and the
third hidden state — came from public discussions with people on Reddit and X,
each recorded with a link in `discussion-record.md`. Where a number is an
assumption rather than a measurement, the code says so at the point of use.
