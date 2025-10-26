"""
System for agentic literature review that's used by other agents.

Implementation uses LangGraph to:
1. Decompose research goals into modular topics
2. Dispatch each topic to GPTResearcher workers in parallel
3. Synthesize topic reports into executive summary
"""

import asyncio
import os
import re
from typing import TypedDict

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import Tone
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, StateGraph

from coscientist.common import load_prompt, validate_llm_response


class LiteratureReviewState(TypedDict):
    """State for the literature review agent."""

    goal: str
    max_subtopics: int
    subtopics: list[str]
    subtopic_reports: list[str]
    meta_review: str


def parse_topic_decomposition(markdown_text: str) -> list[str]:
    """
    Parse the topic decomposition markdown into strings.

    Parameters
    ----------
    markdown_text : str
        The markdown output from topic_decomposition prompt

    Returns
    -------
    list[str]
        Parsed subtopics strings
    """
    # Split by subtopic headers (### Subtopic N)
    sections = re.split(r"### Subtopic \d+", markdown_text)
    return [section.strip() for section in sections[1:]]


def _topic_decomposition_node(
    state: LiteratureReviewState,
    llm: BaseChatModel,
) -> LiteratureReviewState:
    """
    Node that decomposes the research goal into focused subtopics.
    """
    prompt = load_prompt(
        "topic_decomposition",
        goal=state["goal"],
        max_subtopics=state["max_subtopics"],
        subtopics=state.get("subtopics", ""),
        meta_review=state.get("meta_review", ""),
    )
    response = llm.invoke(prompt)
    response_content = validate_llm_response(
        response=response,
        agent_name="literature_review_topic_decomposition",
        prompt=prompt,
        context={
            "goal": state["goal"],
            "max_subtopics": state["max_subtopics"]
        }
    )

    # Parse the topics from the markdown response
    subtopics = parse_topic_decomposition(response_content)

    if not subtopics:
        raise ValueError("Failed to parse any topics from decomposition response")

    if state.get("subtopics", False):
        subtopics = state["subtopics"] + subtopics

    return {"subtopics": subtopics}


async def _write_subtopic_report(subtopic: str, main_goal: str) -> str:
    """
    Conduct research for a single subtopic using GPTResearcher.

    Parameters
    ----------
    subtopic : str
        The subtopic to research
    main_goal : str
        The main research goal for context

    Returns
    -------
    str
        The research report
    """
    # Create a focused query combining the research focus and key terms
    researcher = GPTResearcher(
        query=subtopic,
        report_type="subtopic_report",
        report_format="markdown",
        parent_query=main_goal,
        verbose=True,
        tone=Tone.Objective,
        config_path=os.path.join(os.path.dirname(__file__), "researcher_config.json"),
    )

    # Conduct research and generate report with timeout
    try:
        _ = await asyncio.wait_for(researcher.conduct_research(), timeout=180.0)
        report = await asyncio.wait_for(researcher.write_report(), timeout=60.0)
        return report
    except asyncio.TimeoutError:
        return f"# Research Timeout\n\nResearch for subtopic '{subtopic}' timed out after 180 seconds. Web scraping is taking too long."
    except Exception as e:
        return f"# Research Error\n\nError researching subtopic '{subtopic}': {str(e)}"


async def _parallel_research_node(
    state: LiteratureReviewState,
) -> LiteratureReviewState:
    """
    Node that conducts parallel research for all subtopics using GPTResearcher.
    """
    subtopics = state["subtopics"]
    main_goal = state["goal"]

    # Create research tasks for all subtopics
    research_tasks = [_write_subtopic_report(topic, main_goal) for topic in subtopics]

    # Execute all research tasks in parallel with hard timeout
    # Each task has 180s timeout, so 5 subtopics * 180s = 900s max
    try:
        subtopic_reports = await asyncio.wait_for(
            asyncio.gather(*research_tasks, return_exceptions=True),
            timeout=900.0  # 15 minutes hard deadline for all research
        )
        # Filter out exceptions and use timeout messages
        subtopic_reports = [
            report if not isinstance(report, Exception) 
            else f"# Research Error\n\nError: {str(report)}"
            for report in subtopic_reports
        ]
    except asyncio.TimeoutError:
        subtopic_reports = [
            f"# Research Timeout\n\nResearch for subtopic '{topic}' timed out after 15 minutes."
            for topic in subtopics
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to conduct research for subtopics: {str(e)}")

    if state.get("subtopic_reports", False):
        subtopic_reports = state["subtopic_reports"] + subtopic_reports

    return {"subtopic_reports": subtopic_reports}


def build_literature_review_agent(llm: BaseChatModel) -> StateGraph:
    """
    Builds and configures a LangGraph for literature review.

    Parameters
    ----------
    llm : BaseChatModel
        The language model to use for topic decomposition and executive summary.

    Returns
    -------
    StateGraph
        A compiled LangGraph for the literature review agent.
    """
    graph = StateGraph(LiteratureReviewState)

    # Add nodes
    graph.add_node(
        "topic_decomposition",
        lambda state: _topic_decomposition_node(state, llm),
    )

    graph.add_node(
        "parallel_research",
        _parallel_research_node,
    )

    graph.add_edge("topic_decomposition", "parallel_research")
    graph.add_edge("parallel_research", END)

    graph.set_entry_point("topic_decomposition")

    return graph.compile()
