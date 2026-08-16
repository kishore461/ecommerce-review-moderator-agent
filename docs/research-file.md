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

- **@julianmcauley (Julian McAuley):** Professor whose research focuses on massive e-commerce datasets, review analysis, and opinion spam.
- **@yejinchoi (Yejin Choi):** Pioneer in NLP and deception detection, including foundational work on deceptive opinion spam.
- **@yoavgo (Yoav Goldberg):** NLP researcher who frequently discusses LLM classification reliability and evaluation metrics.
- **@BingLiu_UIC (Bing Liu):** Foundational researcher in sentiment analysis and deceptive review identification.

## Useful Papers, Articles, Repositories, or Datasets

1. **Finding Deceptive Opinion Spam by Any Stretch of the Imagination (Ott et al., 2011):** The foundational paper and dataset for identifying fake reviews using psycholinguistic features.
2. **Amazon Review Data (McAuley et al.):** A massive repository containing millions of product reviews and ratings, useful for understanding real-world text-to-rating relationships.
3. **Justifying Recommendations using Distantly-Labeled Reviews (Ni, Li, McAuley, 2019):** An updated framework for Amazon reviews, useful for analyzing rating-to-text mismatches.
4. **The "Fake Reviews Dataset" (Salminen / Kaggle):** A dataset containing 40,000 fake and real product reviews, excellent for baseline testing.
5. **OpenAI Moderation API Documentation:** Useful for observing how industry-standard content moderation agents handle probability thresholds and categorization.

## Questions to Answer

- **Hidden states:** Which hidden state did I not include? Is it necessary to distinguish between bot-generated spam and human-paid fake reviews?
- **Evidence:** Which evidence changes the belief? Can the agent reliably detect a mismatch between a 5-star rating and highly negative text?
- **Costs:** Which incorrect decision has the highest cost? Is it more damaging to hide a genuine 5-star review for premium silk fabric, or to permit a 1-star competitor sabotage review for dori thread?
- **Human Handoff:** When must the agent ask a human for help (the "warn" or "escalate" action)?
- **Comparability:** Are historical text patterns of spam comparable to modern LLM-generated fake reviews?

## AI Prompts and Important AI Errors

- **Prompt Used:** _"I am a beginner. I want to design an AI agent for this problem: The agent observes a newly submitted customer review text and star rating. It must select permit, warn, hide, or report because whether the post is a genuine customer experience versus a paid spam/competitor fake review is not known. The agent must make decisions when information is not complete. I want to build a utility-based probabilistic agent. Help me prepare my research: Give me technical terms, search queries, 5-10 Reddit communities with reasons, X accounts, questions on hidden states/actions/errors, claims needing testing, and unclear parts."_
- **AI Error 1 (Scope Creep):** The AI initially assumed the agent would have access to user metadata (like IP address, purchase history, and account age). This had to be corrected to fit the strict constraint of the problem statement, which states the agent only observes the review text and the star rating.
- **AI Error 2 (Certainty):** The AI originally presented LLM probability scores as highly accurate, failing to note that language models often suffer from poor calibration (being overly confident in wrong answers), which must be tested for this agent.
