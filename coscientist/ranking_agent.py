"""
Ranking agent
-------------
- Runs tournaments and assigns ELO ratings to hypotheses

More details:
- Newly added hypotheses are added to the tournament with
an ELO rating of 1200.
- Top and bottom ranked hypotheses are evaluated differently.
Two top-ranked hypotheses are paired against each other and
there is a multi-turn scientific debate. Lower ranked hypotheses
are evaluated with a single turn debate. Final output is the number
of the winning hypothesis.
- Based on the Proximity agents graph, similar hypotheses are ranked
against each other. New and top-ranked hypotheses are prioritized.
"""

TOURNAMENT_PROMPT = """
You are an expert evaluator tasked with comparing two hypotheses.

Evaluate the two provided hypotheses (hypothesis 1 and hypothesis 2) and determine which one
is superior based on the specified {idea_attributes}.
Provide a concise rationale for your selection, concluding with the phrase "better idea: <1 or 2>".

Goal: {goal}

Evaluation criteria:
{preferences}

Considerations:
{notes}
Each hypothesis includes an independent review. These reviews may contain numerical scores.
Disregard these scores in your comparative analysis, as they may not be directly comparable across reviews.

Hypothesis 1:
{hypothesis 1}

Hypothesis 2:
{hypothesis 2}

Review of hypothesis 1:
{review 1}

Review of hypothesis 2:
{review 2}

Reasoning and conclusion (end with "better hypothesis: <1 or 2>"):
"""

SIMULATED_DEBATE_PROMPT = """
You are an expert in comparative analysis, simulating a panel of domain experts
engaged in a structured discussion to evaluate two competing hypotheses.
The objective is to rigorously determine which hypothesis is superior based on
a predefined set of attributes and criteria.
The experts possess no pre-existing biases toward either hypothesis and are solely
focused on identifying the optimal choice, given that only one can be implemented.

Goal: {goal}
Criteria for hypothesis superiority:
{preferences}

Hypothesis 1:
{hypothesis 1}

Hypothesis 2:
{hypothesis 2}

Initial review of hypothesis 1:
{review1}

Initial review of hypothesis 2:
{review 2}

Debate procedure:

The discussion will unfold in a series of turns, typically ranging from 3 to 5, with a maximum of 10.

Turn 1: begin with a concise summary of both hypotheses and their respective initial reviews.

Subsequent turns:

* Pose clarifying questions to address any ambiguities or uncertainties.
* Critically evaluate each hypothesis in relation to the stated Goal and Criteria.
This evaluation should consider aspects such as:
- Potential for correctness/validity.
- Utility and practical applicability.
- Sufficiency of detail and specificity.
- Novelty and originality.
- Desirability for implementation.
* Identify and articulate any weaknesses, limitations, or potential flaws in either hypothesis.

Additional notes:
{notes}

Termination and judgment:

Once the discussion has reached a point of sufficient depth (typically 3-5 turns, up to 10 turns)
and all relevant questions and concerns have been thoroughly addressed, provide a conclusive judgment.
This judgment should succinctly state the rationale for the selection.
Then, indicate the superior hypothesis by writing the phrase "better idea: ",
followed by "1" (for hypothesis 1) or "2" (for hypothesis 2).
"""
