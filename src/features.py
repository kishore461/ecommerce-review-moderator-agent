"""
Feature extraction for the review moderation agent.

CONSTRAINT
----------
Every feature here is computed from exactly two observations: the review text
and the star rating. No account age, no purchase history, no photos, no
check-ins, no reviewer history. That constraint comes from the problem
statement and is the whole point of the project, so it is enforced by the
function signature: extract() takes (text, rating) and nothing else.

Features are converted to small integer levels rather than left continuous.
The agent uses a Naive Bayes update, and discrete levels let every likelihood
be estimated by counting and printed in the probability decision record. A
continuous feature would need a distributional assumption that could not be
audited as easily.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict

from prompts import (
    GENERIC_EVALUATIVE,
    EXPERIENCE_MARKERS,
    DETAIL_CONNECTIVES,
    UNIT_TOKENS,
    POSITIVE_WORDS,
    NEGATIVE_WORDS,
)

_WORD_RE = re.compile(r"[a-z']+")
_DIGIT_RE = re.compile(r"\d")


@dataclass(frozen=True)
class Features:
    """Discrete feature levels for one review."""
    specificity: int        # 0 none, 1 some, 2 strong
    generic_praise: int     # 0 none, 1 some, 2 heavy
    length_band: int        # 0 very short, 1 short, 2 medium, 3 long
    polarity_mismatch: int  # 0 consistent, 1 mismatched with the rating
    experience: int         # 0 absent, 1 present
    exclamation: int        # 0 none, 1 some, 2 heavy

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def names() -> list[str]:
        return [
            "specificity",
            "generic_praise",
            "length_band",
            "polarity_mismatch",
            "experience",
            "exclamation",
        ]


def _tokens(text_lower: str) -> list[str]:
    return _WORD_RE.findall(text_lower)


def _count_phrases(text_lower: str, phrases: list[str]) -> int:
    return sum(1 for p in phrases if p in text_lower)


def _count_tokens_in(tokens: list[str], vocabulary: list[str]) -> int:
    vocab = set(vocabulary)
    return sum(1 for t in tokens if t in vocab)


def _specificity_evidence(text: str, text_lower: str, tokens: list[str]) -> int:
    """
    Count concrete, checkable elements.

    Rationale, recorded in discussion-record.md: u/studyhall109 and
    u/XxLogitech98xX (r/Yelp) independently said the separating signal in text
    alone is whether the review names something falsifiable - a dish, a
    quantity, a sequence of events - rather than how positive or negative it
    is.

    KNOWN WEAKNESS: u/XxLogitech98xX later pointed out that a motivated faker
    can lift these specifics from reviews already on the page. Specificity is
    therefore evidence of effort, not evidence of a genuine visit. It is
    expected to separate low-effort fakes and to fail against targeted ones.
    """
    score = 0
    score += min(2, len(_DIGIT_RE.findall(text)))            # quantities
    score += min(2, _count_tokens_in(tokens, UNIT_TOKENS))   # units of measure
    score += min(2, _count_phrases(text_lower, DETAIL_CONNECTIVES))

    # Capitalised words that are not sentence-initial: a crude proxy for named
    # products, brands or people. Deliberately crude - no NER model is used,
    # so this stays reproducible with no downloads.
    sentences = re.split(r"[.!?]\s+", text.strip())
    proper = 0
    for sentence in sentences:
        words = sentence.split()
        for word in words[1:]:
            cleaned = word.strip(".,!?;:'\"()")
            if len(cleaned) > 1 and cleaned[0].isupper() and not cleaned.isupper():
                proper += 1
    score += min(2, proper)
    return score


def _polarity(text_lower: str, tokens: list[str]) -> int:
    """Crude polarity: positive token count minus negative token count."""
    pos = _count_tokens_in(tokens, POSITIVE_WORDS)
    neg = _count_tokens_in(tokens, NEGATIVE_WORDS)
    negators = sum(1 for t in tokens if t in {"not", "never", "no", "dont", "didnt", "wasnt", "isnt"})
    if negators >= 2:
        pos, neg = neg, pos  # heavy negation flips the reading
    return pos - neg


def extract(text: str, rating: float) -> Features:
    """
    Build the discrete feature vector for one review.

    Parameters
    ----------
    text : the review body, exactly as submitted
    rating : the star rating, 1.0 to 5.0

    Nothing else is available to the agent, by design.
    """
    text = "" if text is None else str(text)
    text_lower = text.lower()
    tokens = _tokens(text_lower)
    n_tokens = len(tokens)

    # --- specificity ------------------------------------------------------
    spec_raw = _specificity_evidence(text, text_lower, tokens)
    specificity = 0 if spec_raw == 0 else (1 if spec_raw <= 2 else 2)

    # --- generic evaluative language --------------------------------------
    generic_raw = _count_phrases(text_lower, GENERIC_EVALUATIVE)
    generic_praise = 0 if generic_raw == 0 else (1 if generic_raw <= 1 else 2)

    # --- length -----------------------------------------------------------
    if n_tokens <= 10:
        length_band = 0
    elif n_tokens <= 25:
        length_band = 1
    elif n_tokens <= 60:
        length_band = 2
    else:
        length_band = 3

    # --- polarity vs rating mismatch --------------------------------------
    pol = _polarity(text_lower, tokens)
    if rating >= 4:
        expected = 1
    elif rating <= 2:
        expected = -1
    else:
        expected = 0
    if expected == 1:
        polarity_mismatch = 1 if pol < 0 else 0
    elif expected == -1:
        polarity_mismatch = 1 if pol > 0 else 0
    else:
        polarity_mismatch = 0  # 3-star reviews carry no clear expectation

    # --- first-person experience ------------------------------------------
    experience = 1 if _count_phrases(text_lower, EXPERIENCE_MARKERS) > 0 else 0

    # --- exclamation density ----------------------------------------------
    bangs = text.count("!")
    exclamation = 0 if bangs == 0 else (1 if bangs <= 2 else 2)

    return Features(
        specificity=specificity,
        generic_praise=generic_praise,
        length_band=length_band,
        polarity_mismatch=polarity_mismatch,
        experience=experience,
        exclamation=exclamation,
    )


# Number of levels each feature can take, needed for Laplace smoothing.
FEATURE_LEVELS = {
    "specificity": 3,
    "generic_praise": 3,
    "length_band": 4,
    "polarity_mismatch": 2,
    "experience": 2,
    "exclamation": 3,
}
