"""
Lexical evidence channel.

WHY THIS EXISTS
---------------
The six hand-designed features in features.py are interpretable and they point
the way the public discussions predicted - specificity toward genuine, heavy
generic praise toward fake - but individually they are weak. Fitted alone they
produce a belief that rarely leaves the 0.3-0.7 range, so the agent never
reaches any threshold and defers on essentially every case. That is itself a
result and it is reported, but an experiment in which no policy ever acts
cannot compare two policies.

This module adds a second, purely lexical channel: a multinomial Naive Bayes
model over unigrams, fitted on the fit split only. It is still auditable - the
top discriminative words are written out with the results - and still fully
deterministic, with no model download and no API call.

GUARD AGAINST SWAMPING
----------------------
The lexical log-likelihood ratio is clipped to +/- LLR_CLIP. Without a clip a
long review accumulates hundreds of small word terms and the lexical channel
drowns out the interpretable features entirely, which would make the feature
analysis meaningless. The clip is a modelling choice, not a measurement, and
its value is recorded in the run manifest.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

_WORD_RE = re.compile(r"[a-z']{2,}")

LLR_CLIP = 4.0
MIN_DOC_FREQ = 5


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(("" if text is None else str(text)).lower())


@dataclass
class LexicalModel:
    log_prob: dict = field(default_factory=dict)   # (state, word) -> log P(word|state)
    log_default: dict = field(default_factory=dict)
    vocab: set = field(default_factory=set)
    fitted_on: int = 0

    def fit(self, rows: list[tuple[str, str]], alpha: float = 0.2) -> "LexicalModel":
        """rows: (text, state_value). Only the fit split is ever passed here."""
        doc_freq = Counter()
        counts = defaultdict(Counter)
        totals = Counter()

        tokenised = []
        for text, state in rows:
            toks = tokenize(text)
            tokenised.append((toks, state))
            doc_freq.update(set(toks))

        self.vocab = {w for w, c in doc_freq.items() if c >= MIN_DOC_FREQ}
        for toks, state in tokenised:
            for w in toks:
                if w in self.vocab:
                    counts[state][w] += 1
                    totals[state] += 1

        v = len(self.vocab)
        for state in totals:
            denom = totals[state] + alpha * v
            self.log_default[state] = math.log(alpha / denom)
            for w in self.vocab:
                self.log_prob[(state, w)] = math.log((counts[state][w] + alpha) / denom)
        self.fitted_on = len(rows)
        return self

    def log_lik(self, text: str, state: str) -> float:
        toks = [t for t in tokenize(text) if t in self.vocab]
        if not toks:
            return 0.0
        default = self.log_default.get(state, -20.0)
        return sum(self.log_prob.get((state, t), default) for t in toks)

    def clipped_llr(self, text: str, state: str, reference: str) -> float:
        """
        Log-likelihood ratio of `state` against `reference`, clipped.

        Returned as an additive term for the belief update, so the caller can
        keep the interpretable features and this channel in the same log-space
        sum.
        """
        raw = self.log_lik(text, state) - self.log_lik(text, reference)
        return max(-LLR_CLIP, min(LLR_CLIP, raw))

    def top_words(self, state: str, reference: str, n: int = 25) -> list[tuple[str, float]]:
        """Most discriminative words, for the audit trail."""
        scored = []
        for w in self.vocab:
            a = self.log_prob.get((state, w))
            b = self.log_prob.get((reference, w))
            if a is None or b is None:
                continue
            scored.append((w, a - b))
        scored.sort(key=lambda kv: -kv[1])
        return scored[:n]
