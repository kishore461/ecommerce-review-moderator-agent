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

    # Baseline threshold is tuned on the fit split only.
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
                ag.feedback.record_outcome(
                    cid, d.action,
                    State(r["true_state"]) if d.action == Action.ROUTE else None,
                )
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

        for name, ag in agents.items():
            rate = ag.feedback.overturn_rate()
            if rate is not None:
                print(f"  {name}: human-queue overturn rate {rate:.3f} "
                      f"(genuine among routed)")

    run(test_rows, DEFAULT_PRIOR, "predictions_test.csv")
    run(probe_rows, PROBE_PRIOR, "predictions_probe.csv")

    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_version": MODEL_VERSION,
        "baseline_version": BASELINE_VERSION,
        "baseline_threshold_tuned_on_fit": tuned,
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
    }
    with open(os.path.join(RESULTS, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("run_manifest.json written")


if __name__ == "__main__":
    main()
