"""
Reflection agent
---------------
- Full review with web search
- Simulation review
- Tournament review
- Deep verification

More details:
- Does an initial review to assess the correctness, quality,
and novelty of the hypothesis. Does not use web search -- meant
to be a quick filter of bad ideas.
- Fully reviews a hypothesis with web search
- Deep verification decomposes a hypothesis into constituent
assumptions and sub-assumptions, and checks them for correctness.
Flawed assumptions don't necessarily invalidate an idea, but they
are flagged as areas for refinement/evolution.
- Observation review checks to see if there is unexplained observational
data that would be explained by the hypothesis.
- Simulation does a step-by-step rollout of a proposed mechanism of
action or experiment.
- Tournament review uses the output from the Ranking agent to find
recurring issues and opportunities for improvement.
"""

INITIAL_FILTER_PROMPT = """
"""

DEEP_VERIFICATION_PROMPT = """
"""

SIMULATION_PROMPT = """
"""

TOURNAMENT_REVIEW_PROMPT = """
"""

OBSERVATION_PROMPT = """
You are an expert in scientific hypothesis evaluation. Your task is to analyze the
relationship between a provided hypothesis and observations from a scientific article.
Specifically, determine if the hypothesis provides a novel causal explanation
for the observations, or if they contradict it.

Instructions:

1. Observation extraction: list relevant observations from the article.
2. Causal analysis (individual): for each observation:
a. State if its cause is already established.
b. Assess if the hypothesis could be a causal factor (hypothesis => observation).
c. Start with: "would we see this observation if the hypothesis was true:".
d. Explain if it’s a novel explanation. If not, or if a better explanation exists,
state: "not a missing piece."
3. Causal analysis (summary): determine if the hypothesis offers a novel explanation
for a subset of observations. Include reasoning. Start with: "would we see some of
the observations if the hypothesis was true:".
4. Disproof analysis: determine if any observations contradict the hypothesis.
Start with: "does some observations disprove the hypothesis:".
5. Conclusion: state: "hypothesis: <already explained, other explanations more likely,
missing piece, neutral, or disproved>".

Scoring:
* Already explained: hypothesis consistent, but causes are known. No novel explanation.
* Other explanations more likely: hypothesis *could* explain, but better explanations exist.
* Missing piece: hypothesis offers a novel, plausible explanation.
* Neutral: hypothesis neither explains nor is contradicted.
* Disproved: observations contradict the hypothesis.

Important: if observations are expected regardless of the hypothesis, and don’t disprove it,
it’s neutral.

Article:
{article}

Hypothesis:
{hypothesis}

Response {provide reasoning. end with: "hypothesis: <already explained, other explanations
more likely, missing piece, neutral, or disproved>".)
"""
