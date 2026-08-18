"""
Marker word lists used by the feature extractor and the baseline classifier.

PROVENANCE
----------
These lists were produced with LLM assistance and then edited by hand. That
approach is a design decision recorded in discussion-record.md: a
commenter in r/learnmachinelearning (u/Elegant_Quantity_583) suggested
generating the term list with an LLM rather than hand-writing it, and the
follow-up question in that thread was whether LLM-generated rules inflate
false positives. The baseline in src/baseline.py exists partly to measure
that.

No list here was copied from the test data. Nothing in this module looks at
the label column.

All lists are lowercase and matched on whitespace/punctuation-delimited
tokens or on substrings for the multi-word phrases.
"""

# ---------------------------------------------------------------------------
# Vague evaluative language: praise or complaint with no checkable content.
# u/studyhall109 and u/XxLogitech98xX (r/Yelp) both described this pattern:
# "food is great", "excellent quality", "fast service" with nothing behind it.
# ---------------------------------------------------------------------------
GENERIC_EVALUATIVE = [
    "great product", "great quality", "good quality", "excellent quality",
    "high quality", "poor quality", "bad quality", "great value",
    "highly recommend", "would recommend", "definitely recommend",
    "love it", "love this", "loved it", "i love", "so happy",
    "very happy", "very pleased", "very satisfied", "not satisfied",
    "works great", "works well", "works perfectly", "does the job",
    "fast service", "fast shipping", "quick delivery", "great service",
    "excellent service", "customer service was excellent",
    "waste of money", "waste of time", "do not buy", "don't buy",
    "very disappointed", "not worth it", "worth every penny",
    "best ever", "the best", "amazing product", "awesome product",
    "very nice", "really nice", "very good", "really good",
    "perfect", "terrible", "horrible", "awful", "fantastic",
]

# ---------------------------------------------------------------------------
# First-person experience markers: language that asserts an actual transaction
# or use episode. A person writing about a visit or purchase they did not make
# has less occasion to use these.
# ---------------------------------------------------------------------------
EXPERIENCE_MARKERS = [
    "i ordered", "i bought", "i purchased", "i received", "i returned",
    "it arrived", "arrived", "delivered", "shipped", "package",
    "i asked", "i requested", "i called", "i emailed", "i contacted",
    "when i opened", "after using", "after a week", "after a month",
    "been using", "have been using", "used it for", "using it for",
    "my order", "the order", "replaced", "refund", "exchanged",
    "second one", "bought two", "reordered", "came with",
]

# ---------------------------------------------------------------------------
# Comparative / temporal / conditional language, which tends to accompany a
# real usage history rather than an imagined one.
# ---------------------------------------------------------------------------
DETAIL_CONNECTIVES = [
    "however", "although", "though", "but the", "except", "unless",
    "compared to", "unlike", "instead of", "rather than",
    "at first", "later", "eventually", "after", "before", "until",
    "the first time", "the second time", "every time", "since then",
]

# ---------------------------------------------------------------------------
# Units and measure words. A checkable claim usually carries a quantity.
# ---------------------------------------------------------------------------
UNIT_TOKENS = [
    "inch", "inches", "cm", "mm", "ft", "feet", "foot",
    "lb", "lbs", "pound", "pounds", "kg", "gram", "grams", "oz", "ounce",
    "ml", "litre", "liter", "gallon", "quart",
    "hour", "hours", "minute", "minutes", "day", "days",
    "week", "weeks", "month", "months", "year", "years",
    "dollar", "dollars", "usd", "watt", "watts", "volt", "volts",
    "star", "stars", "degree", "degrees", "percent",
]

# ---------------------------------------------------------------------------
# Sentiment lexicon used only to detect rating/text polarity mismatch.
# Deliberately small and blunt: it is a mismatch detector, not a sentiment
# model. Its weakness on sarcasm is a known and reported limitation.
# ---------------------------------------------------------------------------
POSITIVE_WORDS = [
    "good", "great", "excellent", "perfect", "love", "loved", "loves",
    "amazing", "awesome", "wonderful", "fantastic", "happy", "pleased",
    "satisfied", "beautiful", "sturdy", "comfortable", "recommend",
    "worth", "nice", "best", "easy", "fast", "solid", "durable",
    "pretty", "impressed", "delighted", "superb", "reliable",
]

NEGATIVE_WORDS = [
    "bad", "poor", "terrible", "horrible", "awful", "hate", "hated",
    "broke", "broken", "cheap", "flimsy", "useless", "waste",
    "disappointed", "disappointing", "defective", "damaged", "returned",
    "refund", "uncomfortable", "difficult", "slow", "worse", "worst",
    "never", "stopped", "failed", "leak", "leaked", "rip", "ripped",
    "unusable", "junk", "garbage", "scam", "misleading",
]

# ---------------------------------------------------------------------------
# Baseline keyword list. This is the LLM-assisted spam term list referred to in
# the r/learnmachinelearning discussion. The baseline flags a review as
# suspicious when it contains enough of these and little else.
# ---------------------------------------------------------------------------
BASELINE_SUSPICIOUS_TERMS = GENERIC_EVALUATIVE + [
    "must buy", "must have", "five stars", "5 stars", "10/10",
    "highly satisfied", "great purchase", "good purchase",
    "very well made", "well made", "good product", "nice product",
    "happy with this", "happy with the purchase", "as described",
    "exactly as described", "great deal", "good deal",
]
