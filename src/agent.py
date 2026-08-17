"""
The review moderation agent.

Section 8 of the brief asks for seven parts. They map onto this module as:

  Input        observe() takes review text and star rating, nothing else
  Hidden state State enum below - three states, one of which has no training
               data and is handled by stated assumption, not estimation
  Belief       Belief.posterior - a probability distribution over State
  Action       Action enum - permit, flag with explanation, route to a human,
               hide
  Cost         CostModel - asymmetric, and scaled by the business's review
               volume
  Policy       FixedBandPolicy and ExpectedCostPolicy - the two policies the
               brief requires be compared
  Feedback     record_outcome() - accepts a human verdict for cases that were
               routed, and only for those cases. This is deliberately
               one-sided; see the note on FeedbackLog.

HUMAN REASONING FUNCTION
------------------------
The brief asks for one function borrowed from human reasoning, and warns
against trying to copy all of them. The one implemented here is: identify
uncertainty, and send a high-cost decision to a human rather than guessing.
Both policies can decline to decide. That is the whole of it.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from features import Features, FEATURE_LEVELS, extract

MODEL_VERSION = "agent-0.1.0"


class State(str, Enum):
    """
    The hidden states.

    GENUINE   an independent customer describing their own experience
    FAKE      a paid, competitor or machine-generated review
    SOLICITED a friend or family member of the business

    SOLICITED was added after a discussion in r/Yelp with u/ADrPepperGuy, who
    pointed out that when people say "fake review" they often mean a friend
    writing for a friend rather than paid spam. The visit may genuinely have
    happened and the detail may be true, so the specificity signal cannot
    detect it. See docs/discussion-record.md.

    NOTE ON DATA: the labelled dataset used for the main experiment contains
    only human-written and machine-generated reviews. It has no SOLICITED
    examples, and no paid-human examples either. The likelihoods for SOLICITED
    are therefore assumptions, flagged as such in SOLICITED_ASSUMPTION below,
    and the main experiment collapses to two states. SOLICITED is exercised
    only by the supplementary probe set.
    """
    GENUINE = "genuine"
    FAKE = "fake"
    SOLICITED = "solicited"


class Action(str, Enum):
    PERMIT = "permit"
    FLAG = "flag_with_explanation"
    ROUTE = "route_to_human"
    HIDE = "hide"


# ---------------------------------------------------------------------------
# Priors
# ---------------------------------------------------------------------------
# The real base rate of fake reviews is not known, and no source consulted for
# this project states one that could be checked. The prior is therefore a
# configurable parameter, not a measured quantity. The main experiment runs at
# the base rate of the test sample itself so that calibration is measurable;
# a sensitivity run at a low base rate is reported alongside it.
DEFAULT_PRIOR = {
    State.GENUINE: 0.50,
    State.FAKE: 0.50,
    State.SOLICITED: 0.00,   # no data, excluded from the main experiment
}

PROBE_PRIOR = {
    State.GENUINE: 0.60,
    State.FAKE: 0.30,
    State.SOLICITED: 0.10,
}


# ---------------------------------------------------------------------------
# Assumed likelihoods for the state with no data
# ---------------------------------------------------------------------------
# ASSUMPTION, NOT MEASUREMENT. There are no labelled solicited reviews in the
# dataset, so these cannot be estimated by counting. They encode one claim,
# taken from the r/Yelp discussion: a solicited review describes a real visit,
# so it looks like a genuine review on every feature except that it skews
# positive. If that claim is wrong, every SOLICITED number in the results is
# wrong with it.
SOLICITED_ASSUMPTION = (
    "Solicited reviews are modelled as genuine-like on specificity, length and "
    "experience markers, with elevated generic praise. Not estimated from data - "
    "no labelled examples exist. Sensitive to the assumption that the visit "
    "actually happened."
)


@dataclass
class LikelihoodTable:
    """P(feature level | state), estimated by counting with Laplace smoothing."""
    table: dict = field(default_factory=dict)   # (state, feature, level) -> prob
    counts: dict = field(default_factory=dict)  # for auditing
    fit_n: dict = field(default_factory=dict)

    def fit(self, rows: list[tuple[Features, State]], alpha: float = 1.0) -> "LikelihoodTable":
        counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        totals = defaultdict(int)
        for feats, state in rows:
            totals[state] += 1
            for name, level in feats.as_dict().items():
                counts[state][name][level] += 1

        for state in list(totals):
            for name, n_levels in FEATURE_LEVELS.items():
                denom = totals[state] + alpha * n_levels
                for level in range(n_levels):
                    numer = counts[state][name][level] + alpha
                    self.table[(state, name, level)] = numer / denom

        # Derive the assumed SOLICITED likelihoods from the fitted GENUINE ones.
        if State.GENUINE in totals:
            self._derive_solicited()

        self.counts = {
            str(s): {f: dict(lv) for f, lv in feats.items()} for s, feats in counts.items()
        }
        self.fit_n = {str(k): v for k, v in totals.items()}
        return self

    def _derive_solicited(self) -> None:
        """See SOLICITED_ASSUMPTION. Genuine-like, with praise shifted upward."""
        for name, n_levels in FEATURE_LEVELS.items():
            probs = [self.table[(State.GENUINE, name, lv)] for lv in range(n_levels)]
            if name == "generic_praise":
                # shift mass toward heavier praise
                probs = [probs[0] * 0.5, probs[1] * 1.0, probs[2] * 1.8][:n_levels]
                total = sum(probs)
                probs = [p / total for p in probs]
            for lv in range(n_levels):
                self.table[(State.SOLICITED, name, lv)] = probs[lv]

    def p(self, state: State, feature: str, level: int) -> float:
        return self.table.get((state, feature, level), 1e-6)

    def to_json(self) -> str:
        serialisable = {
            f"{s.value}|{f}|{lv}": p for (s, f, lv), p in self.table.items()
        }
        return json.dumps(
            {
                "model_version": MODEL_VERSION,
                "fit_counts_per_state": self.fit_n,
                "solicited_assumption": SOLICITED_ASSUMPTION,
                "likelihoods": serialisable,
            },
            indent=2,
            sort_keys=True,
        )


@dataclass
class Belief:
    posterior: dict
    log_likelihood_ratios: dict

    def p_not_genuine(self) -> float:
        return self.posterior.get(State.FAKE, 0.0) + self.posterior.get(State.SOLICITED, 0.0)

    def as_dict(self) -> dict:
        return {s.value: round(p, 6) for s, p in self.posterior.items()}


def update_belief(feats: Features, lt: LikelihoodTable, prior: dict,
                  lexical=None, text: str = "") -> Belief:
    """
    Naive Bayes update in log space. Every term is auditable.

    Two evidence channels are combined:
      1. the six interpretable features from features.py
      2. an optional clipped lexical log-likelihood ratio (src/lexical.py)

    Both are additive in log space, so the per-feature contributions stay
    readable in the probability decision record even when the lexical channel
    is doing most of the work.
    """
    log_post = {}
    contributions = {}
    for state, p0 in prior.items():
        if p0 <= 0:
            continue
        total = math.log(p0)
        per_feature = {}
        for name, level in feats.as_dict().items():
            lp = math.log(lt.p(state, name, level))
            per_feature[name] = round(lp, 6)
            total += lp
        if lexical is not None and text:
            ref = State.GENUINE.value
            lex_state = State.GENUINE.value if state == State.SOLICITED else state.value
            lex = 0.0 if lex_state == ref else lexical.clipped_llr(text, lex_state, ref)
            per_feature["lexical_llr"] = round(lex, 6)
            total += lex
        log_post[state] = total
        contributions[state.value] = per_feature

    m = max(log_post.values())
    unnorm = {s: math.exp(v - m) for s, v in log_post.items()}
    z = sum(unnorm.values())
    posterior = {s: v / z for s, v in unnorm.items()}
    return Belief(posterior=posterior, log_likelihood_ratios=contributions)


# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------
@dataclass
class CostModel:
    """
    Asymmetric cost of each action under each true state, in relative units.

    THESE NUMBERS ARE ASSUMPTIONS. No seller answered the direct question about
    what a wrongly removed review actually costs, across two subreddits and one
    X post. What is evidence-based is the *shape*: a commenter in r/Yelp said
    the damage from a wrongly removed review depends heavily on how many
    reviews the business already has, which is why every cost of acting
    wrongly against a genuine review is multiplied by a volume factor. The
    magnitudes are stipulated and should be treated as a sensitivity parameter,
    not a finding.

    volume_factor = min(1, pivot / total_reviews): a shop with few reviews
    feels a removal at close to full cost; a shop with thousands barely does.
    """
    total_reviews: int = 200
    pivot: int = 200

    @property
    def volume_factor(self) -> float:
        return min(1.0, self.pivot / max(1, self.total_reviews))

    def cost(self, action: Action, state: State) -> float:
        v = self.volume_factor
        if state == State.GENUINE:
            return {
                Action.PERMIT: 0.0,
                Action.ROUTE: 1.0,          # a human's time, no harm to the seller
                Action.FLAG: 2.0 * v,       # visible friction, reversible
                Action.HIDE: 10.0 * v,      # the error the seller feels most
            }[action]
        if state == State.FAKE:
            return {
                Action.PERMIT: 5.0,         # deceives buyers, erodes trust
                Action.ROUTE: 1.0,
                Action.FLAG: 1.0,           # caught, some residual exposure
                Action.HIDE: 0.0,
            }[action]
        # SOLICITED: real visit, not independent. Milder harm either way.
        return {
            Action.PERMIT: 2.0,
            Action.ROUTE: 1.0,
            Action.FLAG: 1.5 * v,
            Action.HIDE: 6.0 * v,
        }[action]


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------
class Policy:
    name = "policy"
    version = "0"

    def decide(self, belief: Belief, costs: CostModel) -> tuple[Action, str]:
        raise NotImplementedError


class FixedBandPolicy(Policy):
    """
    Policy A. The bands come from a discussion in r/trustandsafetypros: act
    above 85% belief, route 50-84% to a human queue, permit below 50%.

    The high-confidence action is FLAG, not HIDE. That change came from
    r/Amazonsellercentral, where a seller objected to autonomous hiding and
    preferred a flag carrying an explanation for manual approval. This policy
    therefore never selects HIDE at all.

    The 85% number is borrowed authority, not a measurement - a point made
    directly by u/galvinw in r/learnmachinelearning, who observed that keeping
    a practitioner's number also moves the blame for it.
    """
    name = "fixed_band"
    version = "1.0"
    ACT_THRESHOLD = 0.85
    QUEUE_THRESHOLD = 0.50

    def decide(self, belief: Belief, costs: CostModel) -> tuple[Action, str]:
        p = belief.p_not_genuine()
        if p >= self.ACT_THRESHOLD:
            return Action.FLAG, f"P(not genuine)={p:.3f} >= {self.ACT_THRESHOLD}"
        if p >= self.QUEUE_THRESHOLD:
            return Action.ROUTE, f"{self.QUEUE_THRESHOLD} <= P(not genuine)={p:.3f} < {self.ACT_THRESHOLD}"
        return Action.PERMIT, f"P(not genuine)={p:.3f} < {self.QUEUE_THRESHOLD}"


class ExpectedCostPolicy(Policy):
    """
    Policy B. Choose the action with the lowest expected cost under the current
    belief. No fixed threshold anywhere - the effective threshold falls out of
    the cost matrix and the business's review volume.

    Unlike Policy A this policy is permitted to select HIDE, when the expected
    cost of leaving a review up exceeds the expected cost of removing it. The
    comparison between the two policies is therefore a direct test of the
    design change made after r/Amazonsellercentral.
    """
    name = "expected_cost"
    version = "1.0"

    def decide(self, belief: Belief, costs: CostModel) -> tuple[Action, str]:
        expected = {}
        for action in Action:
            expected[action] = sum(
                belief.posterior.get(state, 0.0) * costs.cost(action, state)
                for state in State
            )
        best = min(expected, key=expected.get)
        detail = ", ".join(f"{a.value}={expected[a]:.3f}" for a in Action)
        return best, f"argmin expected cost [{detail}]"


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
@dataclass
class FeedbackLog:
    """
    Feedback is only ever received for cases routed to a human.

    A review that is permitted generates no signal at all: nobody comes back to
    say a fake slipped through. This asymmetry was raised by u/galvinw in
    r/learnmachinelearning and is recorded as a failure condition, not solved
    here. The consequence is that the live overturn rate can only ever inform
    the false-positive side of the model.
    """
    entries: list = field(default_factory=list)

    def record_outcome(self, case_id: str, action: Action, human_verdict: State | None) -> None:
        if action != Action.ROUTE:
            return  # no observation available; this is the point
        self.entries.append(
            {"case_id": case_id, "action": action.value,
             "human_verdict": human_verdict.value if human_verdict else None}
        )

    def overturn_rate(self) -> float | None:
        if not self.entries:
            return None
        judged = [e for e in self.entries if e["human_verdict"]]
        if not judged:
            return None
        genuine = sum(1 for e in judged if e["human_verdict"] == State.GENUINE.value)
        return genuine / len(judged)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
@dataclass
class Decision:
    case_id: str
    action: Action
    belief: dict
    p_not_genuine: float
    reason: str
    policy: str
    policy_version: str
    model_version: str
    features: dict


class ModerationAgent:
    def __init__(self, likelihoods: LikelihoodTable, policy: Policy,
                 costs: CostModel, prior: dict = None, lexical=None):
        self.likelihoods = likelihoods
        self.policy = policy
        self.costs = costs
        self.prior = prior or DEFAULT_PRIOR
        self.lexical = lexical
        self.feedback = FeedbackLog()

    def observe(self, text: str, rating: float) -> Features:
        """The agent's entire view of the world."""
        return extract(text, rating)

    def decide(self, case_id: str, text: str, rating: float) -> Decision:
        feats = self.observe(text, rating)
        belief = update_belief(feats, self.likelihoods, self.prior,
                               lexical=self.lexical, text=text)
        action, reason = self.policy.decide(belief, self.costs)
        return Decision(
            case_id=case_id,
            action=action,
            belief=belief.as_dict(),
            p_not_genuine=belief.p_not_genuine(),
            reason=reason,
            policy=self.policy.name,
            policy_version=self.policy.version,
            model_version=MODEL_VERSION,
            features=feats.as_dict(),
        )
