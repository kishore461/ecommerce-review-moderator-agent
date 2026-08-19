# AI Research File

## The Problem Statement

The agent observes a newly submitted customer review text and star rating. It must select permit, warn, hide, or report because whether the post is a genuine customer experience versus a paid spam or competitor fake review is not known.

## The Project Objective

To design a utility-based probabilistic AI agent that makes cost-sensitive moderation decisions on e-commerce reviews when information is incomplete.

## Technical Terms

- **Deceptive Opinion Spam:** The formal academic term for fake reviews designed to sound like genuine customer experiences.
- **Utility-Based Agent:** An AI that chooses actions based on maximizing expected utility (or minimizing expected cost), rather than simple rule-matching.
- **Partially Observable Markov Decision Process (POMDP):** A framework for modeling decision-making where the agent cannot directly see the "true" state of the world (e.g., the actual intent of the reviewer).
- **Cost-Sensitive Classification:** A model setup where the penalty for different errors is not equal (e.g., hiding a genuine review is weighted differently than permitting a spam review).
- **Decision Threshold:** The specific probability cutoff (e.g., 85% certainty) required before the agent takes a destructive action like "hide" or "report."
- **Belief State:** The agent's calculated probability distribution over the possible hidden states, given the evidence it has observed.

## Search Queries

- "utility based agent for content moderation"
- "deceptive opinion spam detection benchmark dataset"
- "Bayesian decision theory LLM prompt text classification"
- "cost-sensitive classification e-commerce fake reviews"
- "LLM confidence calibration for sentiment analysis"

## Verified Reddit Communities

1. **r/learnmachinelearning:** Relevant for technical feedback on Bayesian probability models, agent architecture, and academic paper discussions.
2. **r/LanguageTechnology:** Relevant for the NLP aspects of the project, specifically how to parse text for spam patterns and sentiment-rating mismatches.
3. **r/Yelp:** Relevant for understanding the real-world business impact of moderation (e.g., the cost of a false positive vs. a false negative on store sales).
4. **r/Amazonsellercentral:** Relevant for understanding spam patterns targeting specialized materials and craft suppliers (e.g., competitor sabotage on listings for silk fabric or custom woven labels).
5. **r/trustandsafetypros:** Relevant for understanding how human moderation teams set policies and decision thresholds for automated agents.

## Relevant X Accounts

### Verified and followed (25)

| # | Handle | Relevance to this problem |
|---|---|---|
| 1 | @HamelHusain | LLM evals, error analysis, LLM-as-judge design |
| 2 | @sh_reya | Human-AI systems, LLM judges, data validation (CMU) |
| 3 | @lateinteraction | Agent reliability, DSPy pipeline optimisation (MIT) |
| 4 | @zacharylipton | Critic of accuracy-only ML claims; calibration (CMU) |
| 5 | @simonw | Practical LLM reliability and text-detection limits |
| 6 | @tdietterich | Cost-sensitive learning and open-category detection |
| 7 | @noUpside | Adversarial abuse and paid manipulation campaigns |
| 8 | @alexstamos | Platform abuse and enforcement at scale |
| 9 | @eugeneyan | Ex-Amazon applied science; recommender and eval design |
| 10 | @random_walker | AI evaluation and over-claiming in ML results |
| 11 | @jxnlco | Structured outputs and eval pipelines |
| 12 | @ShreyaR | Guardrails AI; validation thresholds on LLM outputs |
| 13 | @pangram | AI-text-detection vendor; its false-positive disputes are this project's error-cost problem |
| 14 | @savipww | Data-driven threads on AI-generated content share |
| 15 | @SStevenWang | AI-generated peer reviews and disclosure thresholds |
| 16 | @OfficialXYO | Open questions on AI detection and trust |
| 17 | @mutant1879 | Critic of AI-detector false positives and burden of proof |
| 18 | @isofunds | Eval-driven development material for agents |
| 19 | @manthanguptaa | Builds agent systems; posts on evals |
| 20 | @florian_jue | Ships coding agents; posts on metric gaming |
| 21 | @Meridian_Fi | Digital trust and agent reliability commentary |
| 22 | @yoavgo | NLP classification reliability and evaluation |
| 23 | @evelyndouek | Content-moderation law and procedural fairness |
| 24 | @onlinenewsporta | Currently reporting on fake five-star Google reviews |
| 25 | @SEOVillas | Local-SEO practitioner view on fake reviews |

The list covers the four categories required: researchers (1–10, 22), engineers and builders (11, 12, 18–21), users and practitioners (13, 24, 25), and critics (14–17, 23). Every account was opened individually on 16 August 2026 and confirmed to have posted recently.

### Engaged since the initial list (not counted in the 25)

These accounts were not on the 16 August list. They surfaced later because the
live technical discussion moved onto a single Pangram thread on 19 August, and
each was replied to rather than merely followed. Links are in
`discussion-record.md`.

| Handle | Why it matters to this problem |
|---|---|
| @max_spero_ | Pangram's founder. Published the exact conditions under which his detector does and does not generalise — the closest thing to a public spec for the failure mode this project has |
| @rosmine | Launched Deft, a model fine-tuned away from "slop" phrasing. States that short prompts get detected as AI, which is this project's own failure mode seen from the generator's side |
| @zeke | Ran a detector across ~100k words of his own writing, so he holds ground truth for his own corpus — the position almost nobody evaluating a detector is in |
| @markvalorian | Argued the detector will be Goodhart-ed out of existence once it becomes a target |
| @cryptotriv | Argues provenance is the real question and style detection is a proxy for it |
| @polsia | Building per-vertical detection with signed provenance; the per-category argument bears directly on limitation 11 |

### Checked and rejected (10)

| Handle | Reason for rejection |
|---|---|
| @julianmcauley | Account exists but has 22 followers and no posts. Not the researcher's working account. |
| @BingLiu_UIC | Account does not exist. |
| @yejinchoi | Wrong handle. The real account is @YejinChoinka, whose last post was January 2026. |
| @tspainfo | Trust & Safety Professional Association. Last post April 2022. |
| @techpolicypress | Last post December 2023. |
| @mmasnick | No visible posts; moved to another platform. |
| @clefourrier | Profile states the account is inactive until December 2026. |
| @Chekkee_ | Content-moderation vendor. Last post January 2026. |
| @marketplacepulse | Account does not exist. |
| @juokaz | E-commerce analyst, but last post March 2026. |

### Note on where the relevant discussion is located

Searches on X for "fake reviews", "opinion spam", "review fraud" and "review bombing" returned almost no technical content — the results were search-engine-optimisation agencies, cryptocurrency scam warnings, entertainment review-bombing disputes, and spam reports directed at Google Maps.

The active technical discussion relevant to this problem concerns false positives in AI-text detectors: users post cases where two detectors return different verdicts on the same text and dispute who carries the burden of proof. That is the same decision problem as this project stated with a different label — classification from text alone, under partial observability, with asymmetric error costs. The accounts followed reflect this finding rather than the initial assumption that content-moderation policy specialists would be reachable on this platform.

## Useful Papers, Articles, Repositories, or Datasets

1. **Finding Deceptive Opinion Spam by Any Stretch of the Imagination (Ott et al., 2011):** The foundational paper and dataset for identifying fake reviews using psycholinguistic features.
2. **Amazon Review Data (McAuley et al.):** A massive repository containing millions of product reviews and ratings, useful for understanding real-world text-to-rating relationships.
3. **Justifying Recommendations using Distantly-Labeled Reviews (Ni, Li, McAuley, 2019):** An updated framework for Amazon reviews, useful for analyzing rating-to-text mismatches.
4. **The "Fake Reviews Dataset" (Salminen / Kaggle):** A dataset containing 40,000 fake and real product reviews, excellent for baseline testing.
5. **OpenAI Moderation API Documentation:** Useful for observing how industry-standard content moderation agents handle probability thresholds and categorization.

### What the preprint actually cites

`paper/references.bib` holds six entries, and they are not the same five as
above. Sources 1, 3 and 4 are cited. Source 2 (Amazon Review Data) is not cited
directly — it reaches this project through Ni et al. 2019, which is. Source 5 is
not cited, because it informed the design conversation rather than any claim in
the paper, and the brief says not to use a reference before reading it. Three
were added while writing, each because a specific claim needed backing:

| Added | Backs |
|---|---|
| Elkan 2001, *The Foundations of Cost-Sensitive Learning* (IJCAI) | The expected-cost policy. The argmin rule and the result that probability thresholds are its special case are his |
| Guo et al. 2017, *On Calibration of Modern Neural Networks* (ICML) | The expected-calibration-error estimator reported as ECE 0.145, and the point that confidence is not calibration |
| Sap et al. 2019, *The Risk of Racial Bias in Hate Speech Detection* (ACL) | Limitation 17. Cited because it names an untested risk in this system, not because anything here was tested for it |

## Questions to Answer

- **Hidden states:** Which hidden state did I not include? Is it necessary to distinguish between bot-generated spam and human-paid fake reviews?
  - *Partially answered (r/Yelp, u/ADrPepperGuy, 17 Aug):* a third state was missing entirely — the **non-independent solicited review**, written by a friend or family member of the business. The visit genuinely happened and the detail is real, so it is neither a genuine independent customer nor a paid fake. It is invisible to the specificity signal for exactly that reason.
- **Evidence:** Which evidence changes the belief? Can the agent reliably detect a mismatch between a 5-star rating and highly negative text?
  - *Partially answered (r/Yelp, u/studyhall109 and u/XxLogitech98xX, 17 Aug):* **specificity** appears to be a stronger text-only signal than rating/sentiment mismatch. Genuine reviews name falsifiable detail — a dish, a quantity, a sequence of events — while planted reviews stay generic, and this holds on positive reviews as well as negative ones. Still to test on my own data.
- **Costs:** Which incorrect decision has the highest cost? Is it more damaging to hide a genuine 5-star review for premium silk fabric, or to permit a 1-star competitor sabotage review for dori thread?
- **Human Handoff:** When must the agent ask a human for help (the "warn" or "escalate" action)?
- **Comparability:** Are historical text patterns of spam comparable to modern LLM-generated fake reviews?

## AI Prompts and Important AI Errors

- **Prompt Used:** _"I am a beginner. I want to design an AI agent for this problem: The agent observes a newly submitted customer review text and star rating. It must select permit, warn, hide, or report because whether the post is a genuine customer experience versus a paid spam/competitor fake review is not known. The agent must make decisions when information is not complete. I want to build a utility-based probabilistic agent. Help me prepare my research: Give me technical terms, search queries, 5-10 Reddit communities with reasons, X accounts, questions on hidden states/actions/errors, claims needing testing, and unclear parts."_
- **AI Error 1 (Scope Creep):** The AI initially assumed the agent would have access to user metadata (like IP address, purchase history, and account age). This had to be corrected to fit the strict constraint of the problem statement, which states the agent only observes the review text and the star rating.
- **AI Error 2 (Certainty):** The AI originally presented LLM probability scores as highly accurate, failing to note that language models often suffer from poor calibration (being overly confident in wrong answers), which must be tested for this agent.
- **AI Error 3 (Fabricated and inactive X accounts):** The assistant produced four X accounts for this project. On verification, one (@BingLiu_UIC) does not exist, one (@julianmcauley) is an empty 22-follower account rather than the researcher's actual presence, and the handle given for Yejin Choi was wrong — the correct account (@YejinChoinka) has been inactive since January 2026. A second round of suggestions covering trust-and-safety and technology-policy accounts was also largely unusable, as most of those accounts stopped posting between 2022 and 2024. Every profile was opened individually on 16 August 2026 to establish this. The correction was to abandon the assumption that content-moderation policy specialists are reachable on this platform and to follow the AI-evaluation and AI-text-detection community instead, where the equivalent technical discussion is active. **Lesson: an AI-supplied handle is a claim to check, not a source.**
- **AI Error 4 (Unverified method assumption):** In drafting a public comment I let an assumption about a cited study go unchecked — that three AI detectors had their confidence scores averaged together. The study's author (@savipww) corrected this publicly: each detector was binarised on its own rule before combining, so scores were never averaged. The error was mine to own in public, and it is recorded here because the underlying lesson is the one this project is about — a plausible reconstruction of a method is not the method.
