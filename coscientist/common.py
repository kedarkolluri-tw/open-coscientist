import os
import re
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

from coscientist.custom_types import ParsedHypothesis
from coscientist.robust_parsing import robust_parse_with_llm

logger = logging.getLogger(__name__)

_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "prompts")),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def load_prompt(name: str, **kwargs) -> str:
    """
    Load a template from the prompts directory and renders
    it with the given kwargs.

    Parameters
    ----------
    name: str
        The name of the template to load, without the .md extension.
    **kwargs: dict
        The kwargs to render the template with.

    Returns
    -------
    str
        The rendered template.
    """
    return _env.get_template(f"{name}.md").render(**kwargs)


def validate_llm_response(response: AIMessage, agent_name: str, prompt: str, context: dict = None) -> str:
    """
    CATASTROPHICALLY VALIDATE LLM response - crashes immediately if empty.
    ALL agents must call this after LLM invocation.

    Parameters
    ----------
    response : AIMessage
        The response from the LLM
    agent_name : str
        Name of the agent (for error reporting)
    prompt : str
        The prompt that was sent
    context : dict, optional
        Additional context for error reporting (goal, state, etc.)

    Returns
    -------
    str
        The validated response content

    Raises
    ------
    RuntimeError
        If response is empty or whitespace-only. ALWAYS crashes - NO RECOVERY.
    """
    response_content = response.content

    # Log response details
    logger.info(f"[{agent_name}] LLM response type: {type(response)}")
    logger.info(f"[{agent_name}] Response content length: {len(response_content) if response_content else 0}")
    logger.info(f"[{agent_name}] Response content preview: {response_content[:200] if response_content else 'EMPTY'}")

    # CATASTROPHIC FAILURE: Empty response is NEVER acceptable
    if not response_content or len(response_content.strip()) == 0:
        error_msg = (
            f"\n{'='*80}\n"
            f"CATASTROPHIC ERROR: LLM returned EMPTY response\n"
            f"{'='*80}\n"
            f"Agent: {agent_name}\n"
            f"Prompt length: {len(prompt)} chars\n"
        )

        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    error_msg += f"{key}: {value[:200]}...\n"
                else:
                    error_msg += f"{key}: {value}\n"

        if hasattr(response, 'response_metadata'):
            error_msg += f"Response metadata: {response.response_metadata}\n"
        if hasattr(response, 'additional_kwargs'):
            error_msg += f"Additional kwargs: {response.additional_kwargs}\n"

        error_msg += (
            f"\n{'='*80}\n"
            f"This should NEVER happen. Empty response means:\n"
            f"  1. LLM API failure\n"
            f"  2. Safety filter blocking ALL content\n"
            f"  3. Prompt construction error\n"
            f"  4. Model configuration error\n"
            f"CRASHING IMMEDIATELY - FIX THIS BEFORE CONTINUING\n"
            f"{'='*80}\n"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Log metadata for non-empty responses
    if hasattr(response, 'response_metadata'):
        logger.info(f"[{agent_name}] Response metadata: {response.response_metadata}")
        finish_reason = response.response_metadata.get('finish_reason')
        if finish_reason == 'MAX_TOKENS':
            logger.warning(
                f"[{agent_name}] Response truncated due to MAX_TOKENS limit.\n"
                f"Content generated: {len(response_content)} chars, Prompt: {len(prompt)} chars\n"
                f"Consider increasing max_tokens in researcher_config.json for complete responses."
            )

    if hasattr(response, 'additional_kwargs'):
        logger.info(f"[{agent_name}] Additional kwargs: {response.additional_kwargs}")

    return response_content


def parse_hypothesis_markdown(markdown_text: str) -> ParsedHypothesis:
    """
    Parse markdown text with # headings to extract Hypothesis, Reasoning, and Assumptions sections.

    Parameters
    ----------
    markdown_text : str
        Markdown text containing sections with # headings for Hypothesis, Reasoning, and Assumptions

    Returns
    -------
    ParsedHypothesis
        Structured output with hypothesis, reasoning, and assumptions fields extracted from markdown
    """
    if "#FINAL REPORT#" in markdown_text:
        markdown_text = markdown_text.split("#FINAL REPORT#")[1]

    # Split the text by # to get sections
    sections = markdown_text.split("#")

    # Initialize fields
    hypothesis = ""
    predictions = []
    assumptions = []

    # Process each section
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Split section into title and content
        lines = section.split("\n", 1)
        if len(lines) < 2:
            continue

        title = lines[0].strip().lower()
        content = lines[1].strip()

        # Match section titles (case-insensitive)
        if "hypothesis" in title:
            hypothesis = content
        elif "prediction" in title:
            predictions = _parse_numbered_list(content)
        elif "assumption" in title:
            assumptions = _parse_numbered_list(content)

    # If predictions or assumptions are missing, try to extract them from hypothesis section
    if not predictions and hypothesis:
        # Sometimes the LLM puts everything in the hypothesis section
        pred_match = re.search(r"(?:# )?Falsifiable Predictions?\s*\n(.*?)(?:# |$)", markdown_text, re.DOTALL | re.IGNORECASE)
        if pred_match:
            predictions = _parse_numbered_list(pred_match.group(1))

    if not assumptions and hypothesis:
        assump_match = re.search(r"(?:# )?Assumptions?\s*\n(.*?)(?:$)", markdown_text, re.DOTALL | re.IGNORECASE)
        if assump_match:
            assumptions = _parse_numbered_list(assump_match.group(1))

    # Fall back to using the full hypothesis text if parsing failed
    if not predictions:
        predictions = ["Failed to parse predictions - please review hypothesis manually"]
    if not assumptions:
        assumptions = ["Failed to parse assumptions - please review hypothesis manually"]

    assert hypothesis, f"Hypothesis section is required: {markdown_text[:500]}"

    return ParsedHypothesis(
        hypothesis=hypothesis, predictions=predictions, assumptions=assumptions
    )


def parse_hypothesis_with_llm(
    llm: BaseChatModel,
    text: str,
    use_robust_parsing: bool = True
) -> ParsedHypothesis:
    """
    Parse hypothesis using LLM-based structured output (RECOMMENDED).

    This method is more robust than regex-based parsing because:
    1. Uses structured output (JSON) directly from LLM
    2. Has self-healing retry logic if parsing fails
    3. Handles token limits by intelligent compaction
    4. Uses semantic understanding, not brittle regex patterns

    Parameters
    ----------
    llm : BaseChatModel
        The language model to use for parsing
    text : str
        Text containing hypothesis to parse
    use_robust_parsing : bool
        If True, uses robust_parse_with_llm with fallbacks (default: True)

    Returns
    -------
    ParsedHypothesis
        Parsed hypothesis with structured fields

    Raises
    ------
    RuntimeError
        If parsing fails after all retry attempts
    """
    instruction = """Extract the scientific hypothesis from this text.
The hypothesis should include:
- The main hypothesis statement
- Falsifiable predictions that could test the hypothesis
- Underlying assumptions

If any section is missing, extract what is available."""

    if use_robust_parsing:
        return robust_parse_with_llm(
            llm=llm,
            text=text,
            output_model=ParsedHypothesis,
            instruction=instruction
        )
    else:
        # Direct structured output without fallbacks
        structured_llm = llm.with_structured_output(ParsedHypothesis)
        from langchain_core.messages import HumanMessage, SystemMessage
        return structured_llm.invoke([
            SystemMessage(content=instruction),
            HumanMessage(content=text)
        ])


def _parse_numbered_list(content: str) -> list[str]:
    """
    Parse a numbered list from text content into a list of strings.

    Parameters
    ----------
    content : str
        Text containing a numbered list (e.g., "1. First item\n2. Second item")

    Returns
    -------
    list[str]
        List of individual items with numbering removed
    """
    if not content.strip():
        return []

    lines = content.split("\n")
    items = []

    # Regex to match various numbering formats: 1., 1), 1-, etc.
    number_pattern = re.compile(r"^\s*\d+[\.\)\-]\s*(.+)", re.MULTILINE)

    current_item = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with a number
        match = number_pattern.match(line)
        if match:
            # If we have a current item, add it to the list
            if current_item:
                items.append(current_item.strip())
            # Start new item
            current_item = match.group(1)
        else:
            # This line is a continuation of the current item
            if current_item:
                current_item += " " + line
            else:
                # Handle case where first line doesn't start with a number
                current_item = line

    # Add the last item
    if current_item:
        items.append(current_item.strip())

    return items
