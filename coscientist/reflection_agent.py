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

from typing import TypedDict

from langchain.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, StateGraph

from coscientist.common import load_prompt


class ReflectionState(TypedDict):
    """
    Represents the state of the reflection process.

    Parameters
    ----------
    hypothesis: str
        The hypothesis being evaluated
    passed_initial_filter: bool
        Whether the hypothesis passed the initial desk rejection filter
    verification_result: str
        The result of the deep verification process
    """

    hypothesis: str
    initial_filter_assessment: str
    passed_initial_filter: bool
    verification_result: str


def desk_reject_node(state: ReflectionState, llm: BaseChatModel) -> ReflectionState:
    """
    Evaluates a hypothesis using the desk_reject.md prompt to determine if it
    should proceed for deeper analysis.

    Parameters
    ----------
    state: ReflectionState
        The current state of the reflection process
    llm: BaseChatModel
        The language model to use for evaluation

    Returns
    -------
    ReflectionState
        Updated state with the passed_initial_filter field updated
    """
    prompt = load_prompt("desk_reject", hypothesis=state["hypothesis"])
    response = llm.invoke(prompt)
    passed = "pass" in response.content.split("FINAL EVALUATION:")[-1].lower()

    return {
        **state,
        "passed_initial_filter": passed,
        "initial_filter_assessment": response.content,
    }


def deep_verification_node(
    state: ReflectionState, llm: BaseChatModel
) -> ReflectionState:
    """
    Performs deep verification of a hypothesis using the deep_verification.md prompt.

    Parameters
    ----------
    state: ReflectionState
        The current state of the reflection process
    llm: BaseChatModel
        The language model to use for verification

    Returns
    -------
    ReflectionState
        Updated state with the verification_result field populated
    """
    prompt = load_prompt("deep_verification", hypothesis=state["hypothesis"])
    response = llm.invoke(prompt)

    return {**state, "verification_result": response.content}


def build_reflection_agent(llm: BaseChatModel):
    """
    Builds and configures a LangGraph for the reflection agent process.

    The graph has two nodes:
    1. desk_reject: Evaluates if a hypothesis is worth deeper analysis
    2. deep_verification: Performs detailed verification of hypotheses that pass initial filtering

    Parameters
    ----------
    llm: BaseChatModel
        The language model to use for both nodes

    Returns
    -------
    StateGraph
        A compiled LangGraph for the reflection agent
    """
    graph = StateGraph(ReflectionState)

    # Add nodes
    graph.add_node("desk_reject", lambda state: desk_reject_node(state, llm))
    graph.add_node(
        "deep_verification", lambda state: deep_verification_node(state, llm)
    )

    # Define transitions
    def route_after_desk_reject(state: ReflectionState):
        if state["passed_initial_filter"]:
            return "deep_verification"
        return END

    graph.add_conditional_edges(
        "desk_reject",
        route_after_desk_reject,
        {"deep_verification": "deep_verification", END: END},
    )

    graph.add_edge("deep_verification", END)

    # Set entry point
    graph.set_entry_point("desk_reject")

    return graph.compile()
