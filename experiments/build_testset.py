"""
Build the fit split, the held-out test set and the supplementary probe set.

Run this before run_experiment.py. It is fully deterministic: the seed is
fixed, so the same 40 test cases come out every time.

Outputs
-------
data/fit_set.csv    used to estimate likelihoods and tune the baseline
data/test_set.csv   40 held-out cases, the main experiment
data/probe_set.csv  12 hand-written cases, reported separately

WHY THE MAIN SET IS 40
----------------------
The brief asks for 30 to 50 labelled or simulated cases. 40 sits inside that
window. The probe set is not counted towards it - it is a diagnostic, and
padding the required count with cases written by the author would defeat the
purpose of using externally labelled data in the first place.

WHAT THE LABELS ACTUALLY MEAN
-----------------------------
The Kaggle dataset labels rows CG (computer-generated) or OR (original human).
That is machine-written versus human-written. It is NOT paid-human-fake versus
genuine, which is what the problem statement is about. The dataset therefore
tests one corner of the FAKE state and says nothing about paid human fakes or
about solicited reviews. This is recorded as a limitation, not worked around.
"""

from __future__ import annotations

import csv
import os
import random
import sys

SEED = 20260817
N_TEST = 40
N_FIT = 6000

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
SOURCE = os.path.join(DATA, "fake reviews dataset.csv")


def load_source() -> list[dict]:
    if not os.path.exists(SOURCE):
        sys.exit(
            f"Source dataset not found at {SOURCE}\n"
            "Download the Fake Reviews Dataset (Salminen et al.) from Kaggle and "
            "place it there as 'fake reviews dataset.csv'."
        )
    rows = []
    with open(SOURCE, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            text = (r.get("text_") or "").strip()
            if not text:
                continue
            rows.append({
                "text": text,
                "rating": float(r["rating"]),
                "category": r.get("category", ""),
                "source_label": r["label"],                    # CG or OR
                "true_state": "fake" if r["label"] == "CG" else "genuine",
            })
    return rows


def stratified_sample(rows: list[dict], n: int, rng: random.Random) -> list[dict]:
    """Half genuine, half fake, spread across the rating scale."""
    by_state = {"genuine": [], "fake": []}
    for r in rows:
        by_state[r["true_state"]].append(r)
    picked = []
    per_state = n // 2
    for state, pool in by_state.items():
        by_rating = {}
        for r in pool:
            by_rating.setdefault(r["rating"], []).append(r)
        ratings = sorted(by_rating)
        per_rating = max(1, per_state // len(ratings))
        chosen = []
        for rating in ratings:
            rng.shuffle(by_rating[rating])
            chosen.extend(by_rating[rating][:per_rating])
        rng.shuffle(chosen)
        picked.extend(chosen[:per_state])
    rng.shuffle(picked)
    return picked


# ---------------------------------------------------------------------------
# Supplementary probe set
# ---------------------------------------------------------------------------
# These twelve cases are written by hand to exercise the failure modes that
# came out of the public discussions. They are SYNTHETIC. They are reported
# separately from the main results and never mixed into the 40, because cases
# written by the author to test the author's own theory cannot also serve as
# independent evidence that the theory works.
#
# probe_kind records which failure mode each case targets.
PROBE_CASES = [
    # --- solicited: real visit, real detail, not independent -----------------
    ("Ordered the ribeye for my brother-in-law's opening night. Came out at a "
     "perfect medium rare and the kitchen sent out extra bread when they saw we "
     "were waiting. Been going since they opened in March.", 5.0, "solicited",
     "solicited_specific"),
    ("My sister runs the front of house here and I eat here most Fridays. The "
     "carbonara is genuinely good, and they fixed the noise problem by adding "
     "panels to the back wall about two months ago.", 5.0, "solicited",
     "solicited_specific"),

    # --- harvested specificity: details lifted from other reviews ------------
    ("The lifetime sharpening on the custom knives is a great value and the "
     "craftsmanship is on another level. Worth every penny. Ask for the flagship "
     "model.", 5.0, "fake", "harvested_specificity"),
    ("Parking was easy, the appetizer came out in about ten minutes, and the "
     "entree was excellent. Highly recommend to anyone in the area.", 5.0, "fake",
     "harvested_specificity"),

    # --- sarcasm and rating mismatch ----------------------------------------
    ("Absolutely wonderful. Truly a fantastic experience waiting fifty minutes "
     "for a cold sandwich. Perfect.", 1.0, "genuine", "sarcasm_mismatch"),
    ("Terrible, awful, I hated every second of having to admit this is the best "
     "pizza in the city and now I have to drive here every week.", 5.0, "genuine",
     "sarcasm_mismatch"),

    # --- genuine but terse: the false-positive risk --------------------------
    ("Works. Fine.", 4.0, "genuine", "genuine_terse"),
    ("Good product, arrived on time.", 5.0, "genuine", "genuine_terse"),

    # --- low-effort fake: what specificity should catch ---------------------
    ("Great product, great quality, highly recommend! Love it! Best purchase "
     "ever!", 5.0, "fake", "low_effort_fake"),
    ("Excellent quality and great value. Very happy with this purchase. Would "
     "recommend.", 5.0, "fake", "low_effort_fake"),

    # --- genuine detailed complaint -----------------------------------------
    ("I asked for no cheese and it arrived covered in cheese. Sent it back, the "
     "second one had cheese too. Forty minutes for a sandwich I could not eat.",
     1.0, "genuine", "genuine_specific_negative"),

    # --- competitor sabotage: vague, emotional, one star ---------------------
    ("Do not waste your money here. Worst place in town. Absolutely terrible, "
     "never going back.", 1.0, "fake", "vague_negative_fake"),
]


def write_csv(path: str, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def main() -> None:
    rng = random.Random(SEED)
    rows = load_source()
    print(f"loaded {len(rows)} source rows")

    test = stratified_sample(rows, N_TEST, rng)
    test_texts = {r["text"] for r in test}

    remaining = [r for r in rows if r["text"] not in test_texts]
    rng.shuffle(remaining)
    fit = remaining[:N_FIT]

    for i, r in enumerate(test):
        r["case_id"] = f"T{i:03d}"
    for i, r in enumerate(fit):
        r["case_id"] = f"F{i:05d}"

    probe = []
    for i, (text, rating, state, kind) in enumerate(PROBE_CASES):
        probe.append({
            "case_id": f"P{i:03d}",
            "text": text,
            "rating": rating,
            "category": "probe_synthetic",
            "source_label": "HAND",
            "true_state": state,
            "probe_kind": kind,
        })

    fields = ["case_id", "text", "rating", "category", "source_label", "true_state"]
    write_csv(os.path.join(DATA, "fit_set.csv"), fit, fields)
    write_csv(os.path.join(DATA, "test_set.csv"), test, fields)
    write_csv(os.path.join(DATA, "probe_set.csv"), probe, fields + ["probe_kind"])

    print(f"fit_set.csv    {len(fit)} rows")
    print(f"test_set.csv   {len(test)} rows  "
          f"({sum(1 for r in test if r['true_state']=='fake')} fake, "
          f"{sum(1 for r in test if r['true_state']=='genuine')} genuine)")
    print(f"probe_set.csv  {len(probe)} rows (supplementary, not part of the 40)")


if __name__ == "__main__":
    main()
