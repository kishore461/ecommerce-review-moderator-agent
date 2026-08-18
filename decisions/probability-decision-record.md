# Probability decision record

One case, decided under genuine uncertainty, then re-decided after one new
piece of evidence arrives.

---

## Why this case

Section 10 asks for a case **whose correct state is not known**. Every review in
the labelled dataset has a label, so none of them qualify — using one would mean
pretending not to know something I do know.

The case chosen instead is a real review posted publicly by **u/XxLogitech98xX**
in r/Yelp on 17 August 2026, as an example of a review he considers unhelpful.
He did not say it was fake. Nobody — not him, not me, not Yelp — knows whether
the person who wrote it was a real customer.

> **"Fast service. Excellent quality work. Fair rates"** — 5 stars

Source: [r/Yelp discussion](https://www.reddit.com/r/Yelp/comments/1vq1jl7/comment/p473953/)

**On comparability.** The brief warns against using a large data group merely
because it is easy to find. The 40,432-row Kaggle set was easy to find, and it
labels machine-written versus human-written text — not the question being asked
here. It is used to estimate feature likelihoods, and nothing more. This single
case is a real review from a live 2026 discussion about the exact decision the
agent makes, which is why it was chosen over a convenient labelled row.

---

## The decision record

| Item | Content |
|---|---|
| **Evidence** | Review text: *"Fast service. Excellent quality work. Fair rates"*. Star rating: 5. Nothing else — no account age, no purchase record, no reviewer history. Derived features: specificity 0 (names nothing checkable), generic_praise 2 (heavy — three vague evaluative phrases), length_band 0 (7 tokens, very short), polarity_mismatch 0, experience 0, exclamation 0. |
| **Hidden states** | `genuine` — an independent customer describing a real transaction. `fake` — paid, competitor or machine-generated. `solicited` — a friend or family member of the business; the visit happened, the review is not independent. |
| **Beliefs** | genuine **0.7069**, fake **0.0092**, solicited **0.2840**. Sum = 1.0000. |
| **Event** | The event the platform cares about is *not independent*, which is `fake` ∪ `solicited`. **P(event) = 0.0092 + 0.2840 = 0.2931.** |
| **Actions** | `permit`, `flag_with_explanation`, `route_to_human`, `hide`. |
| **Costs** | Relative units, at an assumed 200 total reviews (volume factor 1.0). Against `genuine`: permit 0, route 1, flag 2, hide 10. Against `fake`: permit 5, route 1, flag 1, hide 0. Against `solicited`: permit 2, route 1, flag 1.5, hide 6. Magnitudes are assumptions; only the volume scaling is evidence-based. |
| **Policy** | Two policies run on the same belief. **A (fixed bands)**: act ≥ 0.85, route 0.50–0.84, permit < 0.50. **B (expected cost)**: choose the action with lowest expected cost. |
| **Decision** | **Both policies: `permit`.** Policy A because 0.2931 < 0.50. Policy B because expected costs are permit **0.614**, route 1.000, flag 1.849, hide 8.772 — permit is cheapest by a wide margin. |
| **Audit data** | Decided 17 August 2026. Data version: Fake Reviews Dataset (Salminen et al.), fit split 6,000 rows, seed 20260817. Model version `agent-0.1.0`. Policy versions `fixed_band 1.0`, `expected_cost 1.0`. Lexical vocabulary 3,835 unigrams, LLR clip ±4.0. Prior used: genuine 0.60, fake 0.30, solicited 0.10. |

### Evidence for the safe state and the unsafe state

The brief asks for both to be sought, not just the one that confirms a hunch.

**Toward `genuine` (safe):** the review is only seven words long. Very short
reviews are strongly associated with human authors in the fit data (log ratio
−3.56 for `genuine` versus −5.60 for `fake` at this length band) — machine-
generated reviews in this dataset are almost never that terse. The lexical
channel is also neutral-to-favourable, contributing −3.03 against `fake`.

**Toward `fake` or `solicited` (unsafe):** it names nothing checkable at all
(specificity 0) and is built entirely from vague evaluative phrases
(generic_praise 2). Both u/studyhall109 and u/XxLogitech98xX independently said
this is what separates a planted review from a real one, and u/XxLogitech98xX
used *this exact review* as his example of the unhelpful pattern.

**Why the belief lands where it does:** the brevity evidence is strong enough to
outweigh the vagueness evidence, so `fake` collapses to 0.0092. But the mass
does not go to `genuine` — it goes to `solicited` (0.2840), because a solicited
review is modelled as genuine-like in length and specificity while skewing
toward praise. **That is an assumption, not a measurement.** If the assumption
about solicited reviews is wrong, 28 percentage points of this belief are wrong.

---

## Adding one new item of evidence

### 1. Prior probability

Carried forward from the decision above:

| State | Prior |
|---|---|
| genuine | 0.7069 |
| fake | 0.0092 |
| solicited | 0.2840 |

### 2. The new evidence

**The identical review text is found verbatim on a different business's
listing.**

**This evidence is outside the agent's stated observation set, and that has to be
said plainly.** The original wording claimed it "stays inside the constraint"
because it is derived from text. A reviewer pointed out that this is wrong:
detecting a verbatim duplicate on another listing requires a cross-listing index
and a database lookup, which the agent as built has no access to (Gemini preprint
review, finding 5). The claim has been withdrawn.

What this section therefore demonstrates is *what would change the belief if the
capability existed*, not something this agent can currently observe. That is
still a legitimate use of a decision record — the brief asks what new evidence
would do — but it is a hypothetical extension, not a property of the system.

The mechanism itself is real: u/XxLogitech98xX described people copying text from
other listings, and had seen a Yelp Elite reuse other people's photos the same
way.

### 3. Likelihood of that evidence under each state

**These are assumptions, and they are the weakest part of this record.** No
measured duplicate-rate statistics were found for review platforms, so three
settings are carried through rather than one, and the conclusion is reported
against all three.

| Likelihood | Conservative | Central | Aggressive |
|---|---|---|---|
| P(duplicate \| genuine) | 0.020 | 0.005 | 0.001 |
| P(duplicate \| fake) | 0.200 | 0.350 | 0.500 |
| P(duplicate \| solicited) | 0.050 | 0.020 | 0.010 |

Reasoning: a real customer occasionally reuses their own wording across
purchases, so P(duplicate | genuine) is small but not zero. A paid or bulk
operation reuses text as a matter of efficiency, so it is high. A friend writing
one review for one business has little reason to copy, so it sits between.

### 4. Posterior

Bayes, worked explicitly at the central setting so it can be checked by hand:

```
prior(genuine)   = 0.706864
prior(fake)      = 0.009178
prior(solicited) = 0.283958

unnormalised(genuine)   = 0.706864 × 0.005 = 0.00353432
unnormalised(fake)      = 0.009178 × 0.350 = 0.00321220
unnormalised(solicited) = 0.283958 × 0.020 = 0.00567916
                                       sum = 0.01242568

posterior(genuine)   = 0.00353432 / 0.01242568 = 0.28444
posterior(fake)      = 0.00321220 / 0.01242568 = 0.25851
posterior(solicited) = 0.00567916 / 0.01242568 = 0.45705
                                          sum  = 1.00000
```

Full precision is shown deliberately. An earlier version of this record printed
the intermediates rounded to five decimal places and then displayed the division
of the *unrounded* values, so the arithmetic as written did not reproduce the
result beneath it (Gemini probability review, finding 1). The values were never
wrong; the presentation was.

| State | Prior | Posterior (central) |
|---|---|---|
| genuine | 0.7069 | **0.2844** |
| fake | 0.0092 | **0.2585** |
| solicited | 0.2840 | **0.4571** |

**P(event) rises from 0.2931 to 0.7156.** One piece of evidence moved the belief
by 42 percentage points — `fake` alone rose 28-fold.

Across all three likelihood settings:

| Setting | P(not genuine) after |
|---|---|
| Conservative | 0.5314 |
| Central | 0.7156 |
| Aggressive | 0.9131 |

### 5. Compare with the decision threshold

Policy A's thresholds are 0.50 (route) and 0.85 (act).

| Setting | P(event) | Crosses 0.50? | Crosses 0.85? |
|---|---|---|---|
| Conservative | 0.5314 | yes | no |
| Central | 0.7156 | yes | no |
| Aggressive | 0.9131 | yes | **yes** |

**The 0.50 threshold is crossed under every setting.** The 0.85 threshold is
crossed only under the most aggressive assumption. So the conclusion "stop
permitting this" is robust to the assumption; the conclusion "act on it" is not.

### 6. The new action

| Policy | Before | After (central) | After (aggressive) |
|---|---|---|---|
| A — fixed bands | `permit` | **`route_to_human`** | **`flag_with_explanation`** |
| B — expected cost | `permit` | **`route_to_human`** | **`route_to_human`** |

Expected costs at the central posterior: route **1.000**, flag 1.513, permit
2.207, hide 5.587.

**The two policies disagree at the aggressive setting.** Policy A flags because
0.9131 clears its band. Policy B still routes, because even at 91% the expected
cost of routing (1.000) beats flagging (1.261) — the residual chance the review
is genuine is not worth the friction. That disagreement is the clearest
illustration in this project of what a fixed threshold discards: it cannot see
that the cost of being wrong changed, only that the number crossed a line.

---

## What this case shows

1. **One piece of text-only evidence changed the decision.** Permit became
   route, under every likelihood setting tried. The agent did not need account
   metadata to change its mind.
2. **The belief moved into the third hidden state, not the second.** Most of the
   posterior mass landed on `solicited` (0.4571), not `fake` (0.2585). Since
   `solicited` has no data behind it, the state driving the decision is the one
   supported only by an assumption. That is uncomfortable and it is the honest
   reading.
3. **Robustness differs by threshold.** Routing is justified across the whole
   assumption range. Acting is justified only at the extreme end. If this record
   argued for acting, it would be arguing beyond its evidence.
4. **The prior mattered more than the update.** Starting at 0.9% for `fake`, a
   70:1 likelihood ratio only reached 25.9%. Anyone reading a headline "the
   duplicate proves it's fake" should look at the prior first.

## Limitations of this record

- The likelihood numbers for the duplicate evidence are stipulated, not
  measured. Three settings are reported for that reason.
- The `solicited` likelihoods are an assumption throughout
  (`SOLICITED_ASSUMPTION` in `src/agent.py`), and this case turns out to depend
  on them heavily.
- The cost magnitudes are assumptions; only the volume scaling comes from a
  human source.
- The true state of this review is still unknown, and nothing here establishes
  it. The record documents a decision made under uncertainty, not a finding.
