"""
Score the runs.

The brief says not to report accuracy as the only measurement, and lists the
measurements to use where applicable. This module reports: confusion matrix,
precision, recall, false-positive count, false-negative count, human-review
rate, decision cost, and calibration.

It also pulls out the incorrect decisions for the failure analysis, and names
the failure condition for each one.

Outputs
-------
results/metrics.json
results/metrics.md
results/failures.md
"""

from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from agent import Action, State, CostModel  # noqa: E402

RESULTS = os.path.join(ROOT, "results")
TOTAL_REVIEWS_ASSUMED = 200

# An action counts as "acting against" a review if it restricts or marks it.
ACTING = {Action.FLAG.value, Action.HIDE.value}


def read(name: str) -> list[dict]:
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        sys.exit(f"{path} not found. Run experiments/run_experiment.py first.")
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def confusion(rows: list[dict]) -> dict:
    """
    Positive class = "not genuine". Routed cases are excluded from the
    confusion matrix and counted separately as human review, because the agent
    did not make a decision on them - that is the point of the queue.
    """
    tp = fp = tn = fn = 0
    routed = 0
    for r in rows:
        truth_not_genuine = r["true_state"] != "genuine"
        if r["action"] == Action.ROUTE.value:
            routed += 1
            continue
        acted = r["action"] in ACTING
        if acted and truth_not_genuine:
            tp += 1
        elif acted and not truth_not_genuine:
            fp += 1
        elif not acted and truth_not_genuine:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "routed": routed}


def rates(cm: dict, n_total: int) -> dict:
    tp, fp, fn, tn = cm["tp"], cm["fp"], cm["fn"], cm["tn"]
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision and recall else None)
    decided = tp + fp + tn + fn
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positives": fp,
        "false_negatives": fn,
        "accuracy_on_decided": (tp + tn) / decided if decided else None,
        "human_review_rate": cm["routed"] / n_total if n_total else None,
        "decided_rate": decided / n_total if n_total else None,
    }


def decision_cost(rows: list[dict], costs: CostModel) -> float:
    total = 0.0
    for r in rows:
        total += costs.cost(Action(r["action"]), State(r["true_state"]))
    return total


def calibration(rows: list[dict], bins=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)) -> dict:
    """
    Reliability table plus expected calibration error.

    Only rows carrying a probability are included, so the keyword baseline is
    excluded - it emits no belief. That absence is itself a finding: a system
    with no probability cannot be calibrated, well or badly.
    """
    scored = [r for r in rows if r.get("p_not_genuine") not in ("", None)]
    if not scored:
        return {"note": "no probabilistic output", "bins": [], "ece": None}
    table, ece, n = [], 0.0, len(scored)
    for lo, hi in zip(bins, bins[1:]):
        in_bin = [r for r in scored
                  if lo <= float(r["p_not_genuine"]) < hi
                  or (hi == 1.0 and float(r["p_not_genuine"]) == 1.0)]
        if not in_bin:
            table.append({"bin": f"[{lo:.1f},{hi:.1f})", "n": 0,
                          "mean_p": None, "observed": None})
            continue
        mean_p = sum(float(r["p_not_genuine"]) for r in in_bin) / len(in_bin)
        observed = sum(1 for r in in_bin if r["true_state"] != "genuine") / len(in_bin)
        table.append({"bin": f"[{lo:.1f},{hi:.1f})", "n": len(in_bin),
                      "mean_p": round(mean_p, 4), "observed": round(observed, 4)})
        ece += (len(in_bin) / n) * abs(mean_p - observed)
    return {"bins": table, "ece": round(ece, 4)}


# ---------------------------------------------------------------------------
# Failure conditions
# ---------------------------------------------------------------------------
def name_failure(row: dict) -> str:
    """Give each incorrect decision a named failure condition."""
    truth_not_genuine = row["true_state"] != "genuine"
    acted = row["action"] in ACTING
    kind = row.get("probe_kind") or ""

    if kind:
        return {
            "solicited_specific": "SOLICITED-INVISIBLE: real visit, true detail, not independent",
            "harvested_specificity": "SPECIFICITY-HARVESTED: concrete detail copied from the page",
            "sarcasm_mismatch": "SARCASM-INVERTED: polarity contradicts the rating",
            "genuine_terse": "TERSE-GENUINE: a real reviewer who wrote almost nothing",
            "low_effort_fake": "LOW-EFFORT-FAKE: generic praise, no checkable content",
            "genuine_specific_negative": "SPECIFIC-COMPLAINT: detailed genuine negative",
            "vague_negative_fake": "VAGUE-NEGATIVE-FAKE: emotional one star, no detail",
        }.get(kind, f"PROBE-{kind.upper()}")

    if acted and not truth_not_genuine:
        if float(row["rating"]) >= 4:
            return "GENERIC-PRAISE-COLLISION: a genuine happy customer who wrote nothing specific"
        return "TERSE-GENUINE: a real reviewer who wrote almost nothing"
    if not acted and truth_not_genuine:
        if float(row["rating"]) >= 4:
            return "FLUENT-FAKE: machine text that reads like an ordinary short review"
        return "NEGATIVE-FAKE-MISSED: a hostile fake that resembles a real complaint"
    return "UNCLASSIFIED"


def failures_for(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if r["action"] == Action.ROUTE.value:
            continue
        truth_not_genuine = r["true_state"] != "genuine"
        acted = r["action"] in ACTING
        if acted != truth_not_genuine:
            out.append({**r, "failure_condition": name_failure(r)})
    return out


def evaluate_file(pred_file: str, label: str, costs: CostModel) -> dict:
    rows = read(pred_file)
    systems = sorted({r["system"] for r in rows})
    n_cases = len({r["case_id"] for r in rows})
    report = {"set": label, "n_cases": n_cases, "systems": {}}
    for s in systems:
        sub = [r for r in rows if r["system"] == s]
        cm = confusion(sub)
        report["systems"][s] = {
            "confusion_matrix": cm,
            **rates(cm, len(sub)),
            "total_decision_cost": round(decision_cost(sub, costs), 3),
            "mean_decision_cost": round(decision_cost(sub, costs) / len(sub), 4),
            "calibration": calibration(sub),
            "action_counts": {a.value: sum(1 for r in sub if r["action"] == a.value)
                              for a in Action},
        }
    return report


def fmt(x, nd=3):
    return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def to_markdown(reports: list[dict], costs: CostModel) -> str:
    lines = ["# Results", "",
             f"Cost model: volume factor {costs.volume_factor:.3f} "
             f"(assumed {costs.total_reviews} total reviews). "
             "Positive class is \"not genuine\". Routed cases are excluded from the "
             "confusion matrix and reported as human-review rate.", ""]
    for rep in reports:
        lines += [f"## {rep['set']} ({rep['n_cases']} cases)", "",
                  "| System | TP | FP | TN | FN | Routed | Precision | Recall | "
                  "F1 | Human review | Total cost | ECE |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for name, m in rep["systems"].items():
            cm = m["confusion_matrix"]
            lines.append(
                f"| {name} | {cm['tp']} | {cm['fp']} | {cm['tn']} | {cm['fn']} | "
                f"{cm['routed']} | {fmt(m['precision'])} | {fmt(m['recall'])} | "
                f"{fmt(m['f1'])} | {fmt(m['human_review_rate'])} | "
                f"{fmt(m['total_decision_cost'])} | {fmt(m['calibration'].get('ece'))} |"
            )
        lines.append("")
        for name, m in rep["systems"].items():
            cal = m["calibration"]
            if not cal.get("bins"):
                lines += [f"**{name}** emits no probability, so it cannot be "
                          "calibrated. That is a finding, not an omission.", ""]
                continue
            lines += [f"**{name} — reliability**", "",
                      "| Belief bin | n | Mean predicted | Observed fake rate |",
                      "|---|---|---|---|"]
            for b in cal["bins"]:
                lines.append(f"| {b['bin']} | {b['n']} | {fmt(b['mean_p'])} | "
                             f"{fmt(b['observed'])} |")
            lines += ["", f"Expected calibration error: {fmt(cal['ece'])}", ""]
    return "\n".join(lines)


def highest_cost_section(failures: list[dict], costs: CostModel) -> list[str]:
    """
    The brief asks which error has the highest cost, and why. This computes it
    from the cost model rather than asserting it.
    """
    if not failures:
        return ["## Highest-cost error", "", "No incorrect decisions.", ""]
    scored = sorted(
        failures,
        key=lambda f: costs.cost(Action(f["action"]), State(f["true_state"])),
        reverse=True,
    )
    worst = scored[0]
    worst_cost = costs.cost(Action(worst["action"]), State(worst["true_state"]))

    by_kind = {}
    for f in failures:
        c = costs.cost(Action(f["action"]), State(f["true_state"]))
        key = f"{f['action']} on a {f['true_state']} review"
        by_kind.setdefault(key, []).append(c)

    lines = ["## Highest-cost error", "",
             f"Worst single decision: **{worst['case_id']}** by `{worst['system']}` - "
             f"`{worst['action']}` on a review whose true state is "
             f"`{worst['true_state']}`, costing **{worst_cost:.2f}** units.", "",
             f"> {worst['text'][:300]}{'...' if len(worst['text']) > 300 else ''}", "",
             "| Error type | Count | Cost each | Total |", "|---|---|---|---|"]
    for key, cs in sorted(by_kind.items(), key=lambda kv: -sum(kv[1])):
        lines.append(f"| {key} | {len(cs)} | {cs[0]:.2f} | {sum(cs):.2f} |")
    lines += ["", "**Why this error costs the most.** Hiding a genuine review is the "
              "only action that removes a real customer's words while giving the "
              "seller no route to contest it, and its cost is multiplied by the "
              "volume factor, so a shop with few reviews absorbs nearly the whole "
              "penalty. Permitting a fake is diffuse and shared across many buyers; "
              "hiding a genuine review is concentrated on one business and one "
              "customer at once. This asymmetry is why the fixed-band policy was "
              "restricted to flag-with-explanation after the r/Amazonsellercentral "
              "discussion, and it is the clearest argument against letting the "
              "expected-cost policy select `hide` at all.", ""]
    return lines


def failures_markdown(test_fail: list[dict], probe_fail: list[dict],
                      costs: CostModel = None) -> str:
    lines = ["# Failure analysis", "",
             "Every incorrect decision, with a named failure condition. "
             "Routed cases are not failures - the agent declined to decide, "
             "which is a permitted action.", ""]
    if costs is not None:
        lines += highest_cost_section(test_fail + probe_fail, costs)
    for title, group in (("Held-out test set", test_fail),
                         ("Supplementary probe set", probe_fail)):
        lines += [f"## {title}", ""]
        if not group:
            lines += ["No incorrect decisions.", ""]
            continue
        by_cond = {}
        for f in group:
            by_cond.setdefault(f["failure_condition"], []).append(f)
        for cond, items in sorted(by_cond.items(), key=lambda kv: -len(kv[1])):
            lines += [f"### {cond} ({len(items)})", ""]
            for f in items[:6]:
                p = f.get("p_not_genuine") or "n/a"
                lines += [
                    f"- **{f['case_id']}** · {f['system']} · true state "
                    f"`{f['true_state']}` · rating {f['rating']} · action "
                    f"`{f['action']}` · P(not genuine) {p}",
                    f"  > {f['text'][:220]}{'...' if len(f['text']) > 220 else ''}",
                ]
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    costs = CostModel(total_reviews=TOTAL_REVIEWS_ASSUMED)
    reports = [
        evaluate_file("predictions_test.csv", "Held-out test set", costs),
        evaluate_file("predictions_probe.csv", "Supplementary probe set", costs),
    ]
    with open(os.path.join(RESULTS, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)
    with open(os.path.join(RESULTS, "metrics.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(reports, costs))

    test_fail = failures_for(read("predictions_test.csv"))
    probe_fail = failures_for(read("predictions_probe.csv"))
    with open(os.path.join(RESULTS, "failures.md"), "w", encoding="utf-8") as f:
        f.write(failures_markdown(test_fail, probe_fail, costs))

    print(to_markdown(reports, costs))
    print(f"\n{len(test_fail)} incorrect decisions on the test set, "
          f"{len(probe_fail)} on the probe set -> results/failures.md")


if __name__ == "__main__":
    main()
