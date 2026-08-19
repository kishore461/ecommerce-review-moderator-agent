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

Requires Python 3.11+. The three experiment commands need no third-party
packages, no network access and no API keys. Only `experiments/make_figure.py`,
which builds the preprint figure, needs matplotlib.

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
same source download reproduces every number in `results/` exactly, on Windows
as well as Linux — every generated file is written with `newline="\n"` so the
outputs are byte-identical across platforms rather than merely equal in content.
The one field that always differs is `generated_utc` in
`results/run_manifest.json`, which records when the run happened.

Running the project on a second machine (Windows, Python 3.12) found two real
reproducibility defects that a single-machine run could never surface. Both are
fixed. First, every generated text file was being written with the platform's
native line ending, so the same content produced different bytes on Windows.
Second, `LexicalModel.top_words` iterated a `set` and sorted on score alone, so
words with equal scores came out in a different order on every run — Python
randomises string hashing per process. `results/lexical_top_words.md` therefore
changed on each run while every number in it stayed the same. The sort now falls
back to the word itself.

The source file is not pinned by checksum - see limitation 16.

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
| **Feedback** | `FeedbackLog` — routed cases (queue) and enforcement actions (appeals); permitted reviews still yield nothing |

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

The comparison was intended as a direct test of the design change made after
the r/Amazonsellercentral discussion. It is not one: under this cost matrix
`flag` is weakly dominated by `route` for every belief, so B never flags and its
only enforcement action is hiding. The comparison confounds threshold-versus-cost
with flag-only-versus-hide-only. See limitation 6.

### Baseline

`src/baseline.py` — a flat keyword rule with no belief, no cost model, and no
option to defer. Its term-count threshold is tuned on the fit split to **maximise
F1**; the tuned value and the objective are both recorded in
`results/run_manifest.json`. It emits a count rather than a probability, so no
calibration curve is reported — that count *could* be mapped to one, so the
absence is a choice, not an impossibility.
Its keyword list was generated with LLM assistance, following a suggestion in
r/learnmachinelearning. It cannot settle the follow-up question asked there —
whether LLM-generated rules inflate false positives — because there is no
hand-written control list to compare against; the lexical-only ablation row is
the stronger comparator instead.

---

## The ten design questions

Section 12 of the brief asks ten questions about the selected problem. The
answers below are the ones the built system actually supports, with the file or
number that backs each. Where the honest answer is "it doesn't", that is what
is written.

**1. What can the agent observe?**
The review text and the star rating. Nothing else. This is enforced rather than
promised: `ModerationAgent.observe()` takes `(text, rating)` and has no other
parameter. From those two it derives six discrete features (`src/features.py`)
and one clipped log-likelihood ratio over a 3,835-term unigram vocabulary
(`src/lexical.py`). It never sees account age, purchase history, IP address,
photos, timestamps, or the reviewer's other reviews. The source dataset even
carries a `category` column, and the agent does not read it.

**2. What information is hidden?**
The true state — `genuine`, `fake`, or `solicited` — and everything that would
settle it: whether the reviewer bought the product, whether money changed hands,
whether they know the seller personally, and whether a machine wrote the text.
The labels available for training are not this. They are `CG`/`OR` — machine
versus human authorship — which is a different question, and that mismatch is
limitation 1.

**3. What will a human observe that the agent cannot?**
The reviewer's profile, and they will look at it *first*. u/XxLogitech98xX in
r/Yelp said that under 15 reviews he does not read the review text at all. A
human can also open the product page and see whether a "specific" detail was
lifted from it, spot a photo reused across listings, and — at Yelp — see user
reports feeding the same queue. This produces the failure condition recorded in
`discussion-record.md` as **inverted ordering**: for a human, text is a
tiebreaker after the profile check; for this agent, text is the first and only
filter.

**4. What must the agent remember?**
Fixed at fit time: the likelihood table, the lexical vocabulary, the prior, and
the cost model with its volume factor. Across decisions: `FeedbackLog` entries —
case id, action taken, source (`queue` or `appeal`), and the human verdict.
It does **not** remember the review texts it has already seen, so it cannot
detect that the same text appears twice. That is not a small omission: the
largest belief movement measured anywhere in this project — 0.293 to 0.716 on
`P(not genuine)` — comes from exactly that evidence
(`decisions/probability-decision-record.md`), and the agent as built cannot
observe it.

**5. When must the agent ask a question?**
When the belief lands in the deferral band. Policy A routes at
`0.50 <= p < 0.85`, which is 6 of 40 held-out cases (15%). Policy B routes
whenever routing has the lowest expected cost, which is 11 of 40 (27.5%). The
threshold that matters is not a probability but the review volume: sweeping
`total_reviews` in `results/ablation.md` shows Policy B routing 27.5% of cases
at 200 reviews and **nothing at all** at 20,000, because hiding becomes cheaper
than a person's time. The asking mechanism switches itself off for the largest
sellers.

**6. Which incorrect action can be corrected?**
In order of reversibility: `route_to_human` (nothing has happened yet; it costs
a moderator's time), `flag_with_explanation` (visible friction, reversible on
appeal), `hide` (technically reversible, but this design gives the review's
author no notification and no appeal route, and a review's value is
time-sensitive), and `permit` (correctable in principle if somebody reports it,
uncorrected in practice because nobody comes back to say a fake got through).
Measured on the held-out set, 6.7% of Policy A's enforcement actions and 7.1% of
Policy B's were against reviews a human judged genuine
(`results/run_manifest.json`, `feedback_rates`).

**7. Who has the cost of an incorrect action?**
Four parties, and only three are in the cost model.

| Party | Bears | In `CostModel`? |
|---|---|---|
| Seller | a permitted fake (sabotage), a hidden genuine 5-star | Yes, scaled by volume factor `v` |
| Buyer | deception by a permitted fake | Yes, as `permit` under `fake` = 5.0 |
| Moderator | time spent on routed cases | Yes, flat 1.0, modelled as free, instant and infallible |
| **The review's author** | loses their words, no notice, no appeal | **No — not represented at all** |

The volume factor makes this worse rather than better: the harm to the person
whose review was removed is scaled by the *seller's* review count. The party
harmed is not the party the cost is measured against (limitation 9).

**8. Which evidence changes the belief?**
Measured, not asserted. The lexical channel does nearly all the work: with the
features genuinely removed, recall is 0.765 (A) and 0.867 (B) against 0.778 and
0.867 for the full system. The features alone never reach the acting threshold
at all. Within the features, `length_band` carries the most signal (at its
lowest level, P = 0.0037 under `fake` against 0.0286 under `genuine`), and
`polarity_mismatch` — the star/text mismatch that the project started out
believing in — carries almost none, at a log ratio of roughly 0.05. And for 24
of 40 cases the raw ratio saturates the ±4.0 clip, so the belief there is a step
function of the ratio's sign rather than a response to the evidence's strength.

**9. Is the historical evidence comparable?**
No, in three separate ways, and this is the project's most serious threat to
validity. First, the fit data is machine-generated text versus human text, while
the problem is a *paid human* writing a fake — different question. Second, the
generator is GPT-2; a 2026 fake would be written with a far better model, so the
lexical channel is fit on an artefact that is already obsolete. Third, even
within the dataset the comparison is compromised: at token-Jaccard > 0.30, 11 of
20 test fakes have a near-neighbour in the fit split against 0 of 20 genuine, so
the leakage lands on the positive class and inflates recall specifically. The
one external reference point — the 1.36–1.84% false-positive rate for text-only
detection at scale, from @savipww on X — is from AI-detection of articles, not
review moderation, and is a rough comparison rather than a like-for-like one.

**10. How does the agent learn after an action?**
It does not update. `FeedbackLog` records verdicts, but nothing re-fits the
likelihood table and nothing moves a threshold. What the loop produces is two
measurable rates: the genuine rate inside the queue (0.667 for A, 0.545 for B)
and the appeal overturn rate (0.067 for A, 0.071 for B), both in
`results/run_manifest.json`. Two things have to be said about them. They are
computed by feeding ground truth in as the human verdict, so they are relabelled
labels rather than feedback (limitation 8). And the signal is structurally
one-sided: permitted reviews generate no correction, so this loop can only ever
observe false positives and never false negatives — u/galvinw's point in
r/learnmachinelearning. Any threshold drifted from this telemetry would be
drifting on half the error surface.

---

## Results summary

Held-out test set, 40 cases, 20 genuine and 20 fake.

| System | Precision | Recall | Recall (routed in denom.) | FP | FN | Human review | Total cost | ECE |
|---|---|---|---|---|---|---|---|---|
| baseline_keyword | 0.647 | 0.550 | 0.550 | 6 | 9 | 0% | 68.0 | n/a |
| fixed_band (A) | 0.933 | 0.778 | **0.700** | 1 | 4 | 15% | 42.0 | 0.145 |
| expected_cost (B) | 0.929 | 0.867 | **0.650** | 1 | 2 | 27.5% | 31.0 | 0.145 |

**Both recall columns are legitimate and they measure different things.** The
third excludes routed cases, which flatters a policy that declines: an agent
routing 99% of its input and getting the last 1% right would score perfectly. The
fourth counts routed cases as "not acted on", which penalises a policy for
correctly identifying its own uncertainty — and the baseline cannot route at all,
so only the fourth is like-for-like against it. Under the third, B leads
(0.867 vs 0.778); under the fourth, **A leads (0.700 vs 0.650)**. An earlier
version of this README told the reader to use the fourth and ignore the third;
that was overstated, and both are now reported side by side.

**The cost comparison is circular and should not be read as a result.** Policy B
selects the action minimising expected cost under a given cost model, and is then
scored with that same cost model. "B has lower total cost" is a property of
argmin, not a finding.

Both agent policies beat the baseline on the held-out set **on precision and
recall** — not on cost, which is circular and excluded from that comparison.
**They do not beat it everywhere** — on the 12-case probe set the baseline has
higher recall (0.857 vs 0.333). The probe set is designed to attack the agent's
assumptions, and it succeeds.

**The agent is not well calibrated.** ECE 0.145. The 0.6–0.8 belief band predicts
a mean of 0.696 against an observed 0.200 — but that bin holds five cases, so the
figure is indicative, not established. Bin counts are printed beside every
reliability table for this reason.

**The six hand-designed features contribute almost nothing measurable.** With the
feature terms genuinely omitted, the lexical channel alone reaches recall 0.765
(A) and 0.867 (B), against 0.778 and 0.867 for the full system — a difference of
one case on A and zero on B. On A the features also remove one false positive
(precision 0.933 against 0.867), which is the larger of their two contributions.
Alone they never reach the acting threshold: under Policy A they permit 18 cases
and route the other 22, giving recall 0.000; under Policy B they route all 40.
An earlier version of this
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
   LLR of exactly zero, so `P(solicited)/P(genuine)` is bounded above by 0.382
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
17. **No dialect or demographic bias audit has been run.** The lexical channel is
    a unigram model, and unigram filters in content moderation are known to
    penalise non-standard dialects, ESL syntax and AAVE by scoring them as spam
    or machine-generated. Two of the six features make this worse rather than
    better: `length_band` treats brevity as evidence, and `specificity` rewards
    a particular register of concrete detail. A writer with limited English who
    leaves a short, plain review sits exactly where this model is most confident.
    Nothing here has been tested for that, and it is the most consequential
    untested risk in the project.
18. **`solicited` never enters the main results.** Its prior is zero in
    `DEFAULT_PRIOR`, so the main experiment is a two-state problem; the third
    state appears only in the probe run, under a different prior. That different
    prior is necessary — with zero prior mass the state can never be inferred —
    but it means probe and test numbers are not directly comparable, and it is
    recorded in `run_manifest.json` for that reason.
19. **Ties in the expected-cost policy were previously broken by enum order.**
    They are now broken explicitly toward the least destructive action and the
    tie is noted in the decision reason.

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
  make_figure.py     builds paper/figures/figure1.pdf from results/
data/            source dataset and generated splits
results/         predictions, metrics, failures, audit files
paper/           main.tex, references.bib, figures/, preprint.pdf
decisions/       probability-decision-record.md
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
