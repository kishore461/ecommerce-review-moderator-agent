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
python tests/evaluate.py
```

Every step is seeded and deterministic. Running the three commands on a clean
checkout reproduces every number in `results/` exactly.

### What each step writes

| Step | Output |
|---|---|
| `build_testset.py` | `data/fit_set.csv`, `data/test_set.csv`, `data/probe_set.csv` |
| `run_experiment.py` | `results/predictions_test.csv`, `results/predictions_probe.csv`, `results/likelihoods.json`, `results/lexical_top_words.md`, `results/run_manifest.json` |
| `evaluate.py` | `results/metrics.json`, `results/metrics.md`, `results/failures.md` |

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

| System | Precision | Recall | FP | FN | Human review | Total cost | ECE |
|---|---|---|---|---|---|---|---|
| baseline_keyword | 0.647 | 0.550 | 6 | 9 | 0% | 68.0 | n/a |
| fixed_band (A) | 0.933 | 0.778 | 1 | 4 | 15% | 42.0 | 0.145 |
| expected_cost (B) | 0.929 | 0.867 | 1 | 2 | 27.5% | 31.0 | 0.145 |

Both policies beat the baseline on every measure. Policy B reaches a lower
total decision cost than Policy A by routing roughly twice as many cases to a
human — it buys accuracy with human effort, which is exactly the trade the cost
model was built to expose.

**The agent is not well calibrated.** Expected calibration error is 0.145, and
the 0.6–0.8 belief band is badly overconfident: it predicts a mean of 0.696 and
observes an actual fake rate of 0.200. Reporting accuracy alone would have
hidden this entirely.

Full tables: `results/metrics.md`. Failure analysis: `results/failures.md`.

---

## Limitations

These are material, and they qualify every number above.

1. **The dataset's labels are not the project's hidden states.** The Kaggle set
   labels rows `CG` (computer-generated) and `OR` (original human). That is
   machine-written versus human-written. The problem statement is about a *paid
   human* writing a fake with an incentive. The experiment therefore tests one
   corner of the `fake` state and says nothing at all about paid human fakes.
2. **No data exists for the `solicited` state.** Its likelihoods are derived
   from a stated assumption (`SOLICITED_ASSUMPTION` in `src/agent.py`), not
   estimated from examples. Every solicited number depends on that assumption
   being right.
3. **The cost magnitudes are stipulated.** The *shape* is evidence-based — a
   commenter in r/Yelp said the damage from a wrongly removed review depends on
   the business's total review count, which is why the volume factor exists. The
   actual numbers are assumptions. No seller answered the direct cost question
   across two subreddits and one X post.
4. **The lexical channel partly memorises product vocabulary.** The most
   discriminative unigrams include brand names (`schlage`, `taurus`), which
   means some of its power comes from category artefacts rather than from
   deception. See `results/lexical_top_words.md`.
5. **Specificity is not adversarially robust.** A Yelp reviewer pointed out that
   a motivated faker reads the reviews already on the page and lifts dish names
   and staff names from them. Specificity is evidence of *effort*, not of a real
   visit. The probe set demonstrates this failing directly.
6. **Feedback is one-sided.** Permitted reviews generate no correction signal at
   all, so the live overturn rate can only ever inform the false-positive side.
7. **The probe set is synthetic and author-written.** It is reported separately
   and never mixed into the 40, because cases written to test the author's own
   theory cannot also serve as independent evidence for it.
8. **Sarcasm is unsolved.** The polarity-mismatch feature carries almost no
   signal on this data (log ratio ≈ 0.05), and every sarcasm probe case fails.

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
tests/
  evaluate.py    metrics, calibration, failure analysis
data/            source dataset and generated splits
results/         predictions, metrics, failures, audit files
docs/
  research-file.md      terms, sources, communities, AI errors
  discussion-record.md  every public discussion and what it changed
```

---

## AI use

This code was written with AI assistance. The design decisions it implements —
the probability bands, flag-with-explanation instead of autonomous hide, the
volume-weighted cost matrix, the specificity signal and its fragility, and the
third hidden state — came from public discussions with people on Reddit and X,
each recorded with a link in `docs/discussion-record.md`. Where a number is an
assumption rather than a measurement, the code says so at the point of use.
