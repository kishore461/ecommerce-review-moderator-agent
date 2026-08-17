"""
Baseline classifier.

The brief requires the agent be compared against at least one baseline. This
is that baseline: a flat keyword rule with no belief, no cost model and no
option to defer. It either permits or flags.

It exists to answer a specific question that came out of r/learnmachinelearning,
where a commenter suggested generating the spam term list with an LLM rather
than writing it by hand, and the follow-up question was whether LLM-generated
rules inflate false positives. This baseline is the measurement of that.

It is deliberately not a strawman: the term list is the same one the feature
extractor draws on, and the threshold is tuned on the fit split rather than
guessed, so it gets a fair run.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent import Action
from prompts import BASELINE_SUSPICIOUS_TERMS

BASELINE_VERSION = "baseline-keyword-1.0"


@dataclass
class BaselineDecision:
    case_id: str
    action: Action
    score: int
    reason: str
    policy: str = "baseline_keyword"
    policy_version: str = BASELINE_VERSION


class KeywordBaseline:
    """Flags a review when it contains at least `threshold` suspicious terms."""

    def __init__(self, threshold: int = 2):
        self.threshold = threshold
        self.terms = [t.lower() for t in BASELINE_SUSPICIOUS_TERMS]

    def score(self, text: str) -> int:
        low = ("" if text is None else str(text)).lower()
        return sum(1 for t in self.terms if t in low)

    def decide(self, case_id: str, text: str, rating: float) -> BaselineDecision:
        s = self.score(text)
        act = Action.FLAG if s >= self.threshold else Action.PERMIT
        return BaselineDecision(
            case_id=case_id,
            action=act,
            score=s,
            reason=f"{s} suspicious terms, threshold {self.threshold}",
        )

    def tune(self, rows: list[tuple[str, bool]], candidate_thresholds=range(1, 7)) -> int:
        """
        Pick the threshold with the best F1 on the fit split.

        rows: (text, is_not_genuine)
        The test cases are never seen here.
        """
        best_t, best_f1 = self.threshold, -1.0
        for t in candidate_thresholds:
            tp = fp = fn = 0
            for text, truth in rows:
                pred = self.score(text) >= t
                if pred and truth:
                    tp += 1
                elif pred and not truth:
                    fp += 1
                elif not pred and truth:
                    fn += 1
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            if f1 > best_f1:
                best_t, best_f1 = t, f1
        self.threshold = best_t
        return best_t
