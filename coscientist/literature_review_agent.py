"""
System for agentic literature review that's used by other agents.

Implementation uses LangGraph to:
1. Decompose research goals into modular topics
2. Dispatch each topic to GPTResearcher workers in parallel
3. Synthesize topic reports into executive summary
"""

import asyncio
import logging
import os
import re
from typing import TypedDict

from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import Tone
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, StateGraph

from coscientist.common import load_prompt, validate_llm_response
from coscientist.research_backend import create_research_provider
from coscientist.config_loader import load_researcher_config


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


async def _write_subtopic_report(subtopic: str, main_goal: str, output_dir: str = None) -> str:
    """
    Conduct research for a single subtopic using configurable backend.

    Parameters
    ----------
    subtopic : str
        The subtopic to research
    main_goal : str
        The main research goal for context
    output_dir : str, optional
        Output directory for progress logging

    Returns
    -------
    str
        The research report
    """
    # Load configuration and create research provider
    config = load_researcher_config()
    provider = create_research_provider(config, output_dir or ".")
    
    # Create query combining subtopic and main goal
    query = f"Research: {subtopic}\n\nContext: {main_goal}"
    task_id = f"lit_review_{hash(subtopic)}"
    
    try:
        if provider.supports_background_mode():
            # Start background research
            response_id = await provider.conduct_research(query, task_id)
            
            # Poll for completion
            polling_interval = config.get("OPENAI_DEEP_RESEARCH_POLLING_INTERVAL", 30)
            while True:
                result = await provider.get_result(task_id)
                if result:
                    return result
                await asyncio.sleep(polling_interval)
        else:
            # Blocking mode (GPT-Researcher or Perplexity)
            return await provider.conduct_research(query, task_id)
            
    except asyncio.TimeoutError:
        return f"# Research Timeout\n\nResearch for subtopic '{subtopic}' timed out."
    except Exception as e:
        logging.error(f"Research failed for subtopic '{subtopic}': {e}")
        return f"# Research Error\n\nError researching subtopic '{subtopic}': {str(e)}"


async def _parallel_research_node(
    state: LiteratureReviewState,
    framework=None
) -> LiteratureReviewState:
    """
    Node that conducts parallel research for all subtopics using configured backend.
    """
    from coscientist.progress_events import phase_start, phase_complete, task_start, task_complete
    
    subtopics = state["subtopics"]
    main_goal = state["goal"]
    
    # Get output directory for progress tracking
    output_dir = "."
    if framework and hasattr(framework, 'state_manager'):
        output_dir = framework.state_manager._state._output_dir
    
    # Log phase start
    phase_start("literature_review", f"Researching {len(subtopics)} subtopics", output_dir)
    
    # Create research tasks
    research_tasks = []
    for i, topic in enumerate(subtopics):
        task_id = f"subtopic_{i+1}"
        task_start("literature_review", task_id, topic, output_dir)
        research_tasks.append(_write_subtopic_report(topic, main_goal, output_dir))
    
    # Execute all research tasks in parallel
    try:
        subtopic_reports = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Log completion
        for i, (topic, report) in enumerate(zip(subtopics, subtopic_reports)):
            task_id = f"subtopic_{i+1}"
            progress = int((i+1)/len(subtopics)*100)
            task_complete("literature_review", task_id, "Complete", output_dir, progress=progress)
        
        # Filter out exceptions
        subtopic_reports = [
            report if not isinstance(report, Exception) 
            else f"# Research Error\n\nError: {str(report)}"
            for report in subtopic_reports
        ]
        
        phase_complete("literature_review", f"All {len(subtopics)} subtopics researched", output_dir)
        
    except Exception as e:
        logging.error(f"Parallel research failed: {e}")
        subtopic_reports = [
            f"# Research Error\n\nError researching subtopic '{topic}': {str(e)}"
            for topic in subtopics
        ]
        phase_complete("literature_review", f"Failed: {str(e)}", output_dir)

    if state.get("subtopic_reports", False):
        subtopic_reports = state["subtopic_reports"] + subtopic_reports

    return {"subtopic_reports": subtopic_reports}


def build_literature_review_agent(llm: BaseChatModel, framework=None) -> StateGraph:
    """
    Builds and configures a LangGraph for literature review.

    Parameters
    ----------
    llm : BaseChatModel
        The language model to use for topic decomposition and executive summary.
    framework : CoscientistFramework, optional
        Framework instance for access to research provider

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
        lambda state: _parallel_research_node(state, framework),
    )

    graph.add_edge("topic_decomposition", "parallel_research")
    graph.add_edge("parallel_research", END)

    graph.set_entry_point("topic_decomposition")

    return graph.compile()
