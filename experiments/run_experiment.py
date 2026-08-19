"""
Run the baseline and both agent policies over the held-out test set.

The true label is never passed to the agent. decide() receives only the review
text and the star rating; labels are joined back on afterwards, in this file,
for scoring only.

Outputs
-------
results/predictions_test.csv    every decision on the 40 held-out cases
results/predictions_probe.csv   every decision on the 12 probe cases
results/likelihoods.json        the fitted likelihood table, for auditing
results/run_manifest.json       versions, seed, thresholds, cost parameters
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from agent import (  # noqa: E402
    MODEL_VERSION, State, Action, LikelihoodTable, CostModel,
    FixedBandPolicy, ExpectedCostPolicy, ModerationAgent,
    DEFAULT_PRIOR, PROBE_PRIOR,
)
from baseline import KeywordBaseline, BASELINE_VERSION  # noqa: E402
from features import extract  # noqa: E402
from lexical import LexicalModel, LLR_CLIP, MIN_DOC_FREQ  # noqa: E402

DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(ROOT, "results")
TOTAL_REVIEWS_ASSUMED = 200   # small seller; see CostModel docstring


def read_csv(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        sys.exit(f"{path} not found. Run experiments/build_testset.py first.")
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fit_likelihoods(fit_rows: list[dict]) -> LikelihoodTable:
    pairs = []
    for r in fit_rows:
        feats = extract(r["text"], float(r["rating"]))
        pairs.append((feats, State(r["true_state"])))
    return LikelihoodTable().fit(pairs)


def write_ablation(test_rows, lt, lex, costs) -> None:
    """
    Two checks added in response to the AI reviews (see review-record.md).

    ABLATION - do the six hand-designed features contribute anything, or is the
    lexical channel doing all the work? Answered by running the agent with each
    channel removed in turn.

    BASE RATE - the main experiment runs at a 50% fake prior because that is the
    test sample's own balance. Real base rates are far lower and unknown. This
    sweeps the prior to show how far the headline numbers travel.
    """
    from agent import update_belief, Belief  # noqa: PLC0415
    ACTING = {Action.FLAG.value, Action.HIDE.value}

    def score(prior, use_lex, use_feats, policy, cost_model=None):
        tp = fp = tn = fn = routed = 0
        for r in test_rows:
            f = extract(r["text"], float(r["rating"]))
            b = update_belief(f, lt, prior, lexical=(lex if use_lex else None),
                              text=r["text"], use_features=use_feats)
            a, _ = policy.decide(b, cost_model or costs)
            truth = r["true_state"] != "genuine"
            if a == Action.ROUTE:
                routed += 1
                continue
            acted = a.value in ACTING
            if acted and truth:
                tp += 1
            elif acted and not truth:
                fp += 1
            elif not acted and truth:
                fn += 1
            else:
                tn += 1
        p = tp / (tp + fp) if tp + fp else None
        rec = tp / (tp + fn) if tp + fn else None
        return tp, fp, tn, fn, routed, p, rec

    def fmt(x):
        return "-" if x is None else f"{x:.3f}"

    lines = ["# Ablation and base-rate sensitivity", "",
             "Both checks were added after the AI reviews in `review-record.md`.", "",
             "## Do the six hand-designed features contribute anything?", "",
             "| Channels | Policy | TP | FP | TN | FN | Routed | Precision | Recall |",
             "|---|---|---|---|---|---|---|---|---|"]
    balanced = {State.GENUINE: 0.5, State.FAKE: 0.5, State.SOLICITED: 0.0}
    results_index, base_index = {}, {}
    for label, (ul, uf) in {"features + lexical": (True, True),
                            "lexical only": (True, False),
                            "features only": (False, True)}.items():
        for pol in (FixedBandPolicy(), ExpectedCostPolicy()):
            row = score(balanced, ul, uf, pol)
            results_index[(label, pol.name)] = row
            tp, fp, tn, fn, rt, p, rec = row
            lines.append(f"| {label} | {pol.name} | {tp} | {fp} | {tn} | {fn} | "
                         f"{rt} | {fmt(p)} | {fmt(rec)} |")
    fb_full = results_index[("features + lexical", "fixed_band")]
    fb_lex = results_index[("lexical only", "fixed_band")]
    ec_full = results_index[("features + lexical", "expected_cost")]
    ec_lex = results_index[("lexical only", "expected_cost")]
    feat_only = [v for k, v in results_index.items() if k[0] == "features only"]
    feat_recalls = [v[6] for v in feat_only if v[6] is not None]
    lines += ["",
              "**Reading (computed from the table above, not asserted).** "
              f"With the feature terms genuinely omitted, the lexical channel alone "
              f"reaches recall {fmt(fb_lex[6])} (fixed band) and {fmt(ec_lex[6])} "
              f"(expected cost), against {fmt(fb_full[6])} and {fmt(ec_full[6])} for "
              "the full system. Features alone reach recall "
              f"{', '.join(fmt(r) for r in feat_recalls) or 'n/a'}. "
              "Read the deltas rather than any sentence written in advance.",
              ""]
    lines += [              "", "## How far do the headline numbers travel?", "",
              "| Prior P(fake) | Policy | TP | FP | TN | FN | Routed | Precision | Recall |",
              "|---|---|---|---|---|---|---|---|---|"]
    for pf in (0.5, 0.3, 0.1, 0.05):
        prior = {State.GENUINE: 1 - pf, State.FAKE: pf, State.SOLICITED: 0.0}
        for pol in (FixedBandPolicy(), ExpectedCostPolicy()):
            row = score(prior, True, True, pol)
            base_index[(pf, pol.name)] = row
            tp, fp, tn, fn, rt, p, rec = row
            lines.append(f"| {pf} | {pol.name} | {tp} | {fp} | {tn} | {fn} | "
                         f"{rt} | {fmt(p)} | {fmt(rec)} |")
    lo = base_index[(0.1, "fixed_band")]
    hi = base_index[(0.5, "fixed_band")]
    lo_ec = base_index[(0.1, "expected_cost")]
    hi_ec = base_index[(0.5, "expected_cost")]
    lines += ["",
              "**Reading (computed).** Moving the prior from 0.5 to 0.1 changes "
              f"fixed-band recall {fmt(hi[6])} -> {fmt(lo[6])} and expected-cost "
              f"recall {fmt(hi_ec[6])} -> {fmt(lo_ec[6])}. The headline figures are "
              "conditional on a 50% base rate that no deployment would have.", ""]

    # --- volume factor sweep: the one cost parameter the cost model calls
    # --- evidence-based, and the one never previously varied.
    lines += ["## How far does the cost model travel?", "",
              "`total_reviews` sets the volume factor. Only 200 was ever reported.", "",
              "| total_reviews | volume factor | Policy | permit | flag | route | hide | genuine hidden |",
              "|---|---|---|---|---|---|---|---|"]
    for tr in (200, 1000, 5000, 20000):
        cm = CostModel(total_reviews=tr)
        for pol in (FixedBandPolicy(), ExpectedCostPolicy()):
            counts = {a.value: 0 for a in Action}
            genuine_hidden = 0
            for r in test_rows:
                f = extract(r["text"], float(r["rating"]))
                b = update_belief(f, lt, balanced, lexical=lex, text=r["text"])
                a, _ = pol.decide(b, cm)
                counts[a.value] += 1
                if a == Action.HIDE and r["true_state"] == "genuine":
                    genuine_hidden += 1
            lines.append(
                f"| {tr} | {cm.volume_factor:.2f} | {pol.name} | {counts['permit']} | "
                f"{counts['flag_with_explanation']} | {counts['route_to_human']} | "
                f"{counts['hide']} | {genuine_hidden} |")
    lines += ["",
              "**Reading (computed).** The volume factor divides the cost of acting "
              "wrongly against a genuine review but not the cost of routing, so as a "
              "seller's review count rises, hiding gets cheaper while human review "
              "stays at 1.0. The reported configuration (200 reviews) is the most "
              "conservative point in this range, and that was not previously stated.",
              ""]
    with open(os.path.join(RESULTS, "ablation.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("ablation.md written")


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)

    fit_rows = read_csv("fit_set.csv")
    test_rows = read_csv("test_set.csv")
    probe_rows = read_csv("probe_set.csv")

    lt = fit_likelihoods(fit_rows)
    with open(os.path.join(RESULTS, "likelihoods.json"), "w", encoding="utf-8") as f:
        f.write(lt.to_json())

    lex = LexicalModel().fit([(r["text"], r["true_state"]) for r in fit_rows])
    with open(os.path.join(RESULTS, "lexical_top_words.md"), "w", encoding="utf-8") as f:
        f.write("# Most discriminative unigrams (fit split only)\n\n")
        f.write(f"Vocabulary {len(lex.vocab)} words, min document frequency "
                f"{MIN_DOC_FREQ}, LLR clip +/-{LLR_CLIP}.\n\n")
        for state, label in (("fake", "toward FAKE"), ("genuine", "toward GENUINE")):
            ref = "genuine" if state == "fake" else "fake"
            f.write(f"## {label}\n\n| word | log ratio |\n|---|---|\n")
            for w, s in lex.top_words(state, ref, 25):
                f.write(f"| {w} | {s:+.3f} |\n")
            f.write("\n")

    baseline = KeywordBaseline()
    tuned = baseline.tune([(r["text"], r["true_state"] != "genuine") for r in fit_rows])
    costs = CostModel(total_reviews=TOTAL_REVIEWS_ASSUMED)

    def run(rows: list[dict], prior: dict, out_name: str) -> None:
        agents = {
            "fixed_band": ModerationAgent(lt, FixedBandPolicy(), costs, prior, lexical=lex),
            "expected_cost": ModerationAgent(lt, ExpectedCostPolicy(), costs, prior, lexical=lex),
        }
        records = []
        for r in rows:
            cid, text, rating = r["case_id"], r["text"], float(r["rating"])
            b = baseline.decide(cid, text, rating)
            records.append({
                "case_id": cid, "system": "baseline_keyword",
                "policy_version": b.policy_version,
                "action": b.action.value, "p_not_genuine": "",
                "belief_genuine": "", "belief_fake": "", "belief_solicited": "",
                "reason": b.reason, "true_state": r["true_state"],
                "rating": rating, "probe_kind": r.get("probe_kind", ""),
                "text": text,
            })
            for name, ag in agents.items():
                d = ag.decide(cid, text, rating)
                # Ground truth stands in for a human verdict here. That is a
                # simulation convenience, not feedback - see README limitation 8.
                ag.feedback.record_outcome(cid, d.action, State(r["true_state"]))
                records.append({
                    "case_id": cid, "system": name,
                    "policy_version": d.policy_version,
                    "action": d.action.value,
                    "p_not_genuine": round(d.p_not_genuine, 6),
                    "belief_genuine": d.belief.get("genuine", ""),
                    "belief_fake": d.belief.get("fake", ""),
                    "belief_solicited": d.belief.get("solicited", ""),
                    "reason": d.reason, "true_state": r["true_state"],
                    "rating": rating, "probe_kind": r.get("probe_kind", ""),
                    "text": text,
                })
        fields = ["case_id", "system", "policy_version", "action", "p_not_genuine",
                  "belief_genuine", "belief_fake", "belief_solicited",
                  "true_state", "rating", "probe_kind", "reason", "text"]
        with open(os.path.join(RESULTS, out_name), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(records)
        print(f"{out_name}: {len(records)} decisions over {len(rows)} cases")
        rates = {}
        for name, ag in agents.items():
            q = ag.feedback.genuine_rate_in_queue()
            ap = ag.feedback.appeal_overturn_rate()
            rates[name] = {"genuine_rate_in_queue": q,
                           "appeal_overturn_rate": ap}
            if q is not None:
                print(f"  {name}: genuine rate inside the queue {q:.3f} "
                      f"(prevalence in the ambiguity band, NOT an overturn rate)")
            if ap is not None:
                print(f"  {name}: appeal overturn rate {ap:.3f} "
                      f"(enforcement actions a human judged genuine)")
        return rates

    feedback = {}
    feedback["test"] = run(test_rows, DEFAULT_PRIOR, "predictions_test.csv")
    feedback["probe"] = run(probe_rows, PROBE_PRIOR, "predictions_probe.csv")
    write_ablation(test_rows, lt, lex, costs)

    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_version": MODEL_VERSION,
        "baseline_version": BASELINE_VERSION,
        "baseline_threshold_tuned_on_fit": tuned,
        "baseline_tuning_objective": "max F1 on the fit split",
        "fit_rows": len(fit_rows),
        "test_rows": len(test_rows),
        "probe_rows": len(probe_rows),
        "prior_main": {k.value: v for k, v in DEFAULT_PRIOR.items()},
        "prior_probe": {k.value: v for k, v in PROBE_PRIOR.items()},
        "fixed_band_act_threshold": FixedBandPolicy.ACT_THRESHOLD,
        "fixed_band_queue_threshold": FixedBandPolicy.QUEUE_THRESHOLD,
        "cost_total_reviews_assumed": TOTAL_REVIEWS_ASSUMED,
        "cost_volume_factor": costs.volume_factor,
        "testset_seed": 20260817,
        "lexical_vocab_size": len(lex.vocab),
        "lexical_llr_clip": LLR_CLIP,
        "lexical_min_doc_freq": MIN_DOC_FREQ,
        # Feedback rates were previously printed to stdout only, so the README
        # and review-record cited numbers that were in no committed file.
        # genuine_rate_in_queue is a prevalence, NOT an overturn rate; only
        # appeal_overturn_rate is an overturn. Both are computed by feeding
        # ground truth in as the human verdict - see limitation 8.
        "feedback_rates": feedback,
    }
    with open(os.path.join(RESULTS, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("run_manifest.json written")


if __name__ == "__main__":
    main()
