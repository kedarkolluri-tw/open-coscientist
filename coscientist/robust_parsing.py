"""
Robust, self-healing parsing utilities that use LLMs instead of brittle regex.

Instead of regex-based parsing that fails silently, this module:
1. Uses structured output (JSON) from LLMs directly
2. Has LLM-based extraction as fallback
3. Self-heals by detecting errors and retrying with corrections
4. Handles token limits by intelligent compaction
"""

import logging
from typing import TypeVar, Type, Callable, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class TokenLimitError(Exception):
    """Raised when input exceeds token limits."""
    pass


def extract_with_structured_output(
    llm: BaseChatModel,
    text: str,
    output_model: Type[T],
    instruction: str = None,
    max_retries: int = 3
) -> T:
    """
    Extract structured data from text using LLM with structured output.

    This uses LangChain's with_structured_output() to have the LLM
    directly output the desired Pydantic model. If that fails, it
    uses self-healing retry logic.

    Parameters
    ----------
    llm : BaseChatModel
        The language model to use for extraction
    text : str
        The text to extract from
    output_model : Type[T]
        The Pydantic model class to extract
    instruction : str, optional
        Additional instruction for the LLM
    max_retries : int
        Maximum number of retry attempts (default: 3)

    Returns
    -------
    T
        Extracted structured data

    Raises
    ------
    RuntimeError
        If extraction fails after all retries
    TokenLimitError
        If input is too long even after compaction
    """
    # Create structured output LLM
    structured_llm = llm.with_structured_output(output_model)

    # Build system message
    system_msg = "Extract the requested information from the text."
    if instruction:
        system_msg += f" {instruction}"

    # Get field descriptions from Pydantic model for context
    field_descriptions = []
    for field_name, field_info in output_model.model_fields.items():
        if field_info.description:
            field_descriptions.append(f"- {field_name}: {field_info.description}")

    if field_descriptions:
        system_msg += "\n\nExpected fields:\n" + "\n".join(field_descriptions)

    last_error = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Structured extraction attempt {attempt + 1}/{max_retries}")

            # Try structured extraction
            result = structured_llm.invoke([
                SystemMessage(content=system_msg),
                HumanMessage(content=text)
            ])

            # Validate result
            if isinstance(result, output_model):
                logger.info("✓ Structured extraction successful")
                return result
            else:
                raise ValueError(f"Expected {output_model.__name__}, got {type(result)}")

        except ValidationError as e:
            last_error = e
            logger.warning(f"Validation error on attempt {attempt + 1}: {e}")

            # Add validation feedback for next attempt
            system_msg += f"\n\nPrevious attempt had validation errors: {str(e)}"
            system_msg += "\nPlease ensure all required fields are present and correctly formatted."

        except Exception as e:
            last_error = e
            logger.warning(f"Extraction error on attempt {attempt + 1}: {e}")

            # Check for token limit errors
            if "token" in str(e).lower() and "limit" in str(e).lower():
                logger.warning("Token limit detected, attempting compaction...")
                text = _compact_text(llm, text, output_model)
                continue

            # Generic retry guidance
            system_msg += f"\n\nPrevious attempt failed: {str(e)}"
            system_msg += "\nPlease try again, ensuring proper formatting."

    # All retries failed
    raise RuntimeError(
        f"Failed to extract {output_model.__name__} after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


def extract_with_llm_fallback(
    llm: BaseChatModel,
    text: str,
    output_model: Type[T],
    instruction: str = None
) -> T:
    """
    Extract structured data using LLM semantic understanding (fallback method).

    This method asks the LLM to extract specific information and format
    it as JSON, then parses it into the Pydantic model. This is more
    robust than regex but less direct than with_structured_output().

    Parameters
    ----------
    llm : BaseChatModel
        The language model to use
    text : str
        The text to extract from
    output_model : Type[T]
        The Pydantic model to populate
    instruction : str, optional
        Additional extraction instructions

    Returns
    -------
    T
        Extracted structured data

    Raises
    ------
    RuntimeError
        If extraction and parsing fails
    """
    # Build extraction prompt
    field_descriptions = []
    for field_name, field_info in output_model.model_fields.items():
        desc = field_info.description or field_name
        field_descriptions.append(f'"{field_name}": {desc}')

    prompt = f"""Extract the following information from the text and return it as valid JSON:

{{
  {','.join(field_descriptions)}
}}

Text to extract from:
{text}

Return ONLY the JSON object, no other text."""

    if instruction:
        prompt = f"{instruction}\n\n{prompt}"

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        json_text = response.content.strip()

        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            lines = json_text.split("\n")
            json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text

        # Parse JSON into Pydantic model
        return output_model.model_validate_json(json_text)

    except Exception as e:
        raise RuntimeError(f"LLM fallback extraction failed: {e}")


def _compact_text(
    llm: BaseChatModel,
    text: str,
    target_model: Type[BaseModel],
    target_length: int = None
) -> str:
    """
    Intelligently compact text when hitting token limits.

    Uses LLM to summarize/compress while preserving information
    needed for the target extraction model.

    Parameters
    ----------
    llm : BaseChatModel
        The language model to use for compaction
    text : str
        The text to compact
    target_model : Type[BaseModel]
        The model we're trying to extract (guides compaction)
    target_length : int, optional
        Target character length (default: 50% of original)

    Returns
    -------
    str
        Compacted text

    Raises
    ------
    TokenLimitError
        If text cannot be compacted sufficiently
    """
    if target_length is None:
        target_length = len(text) // 2

    # Build compaction prompt
    field_names = list(target_model.model_fields.keys())
    prompt = f"""Compress the following text to approximately {target_length} characters while preserving all information needed to extract these fields: {', '.join(field_names)}.

Remove redundant information, verbose explanations, and examples, but keep all essential content.

Original text:
{text}

Compressed version:"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        compacted = response.content.strip()

        logger.info(f"Compacted text from {len(text)} to {len(compacted)} chars")

        if len(compacted) >= len(text):
            logger.warning("Compaction did not reduce size, using truncation")
            return text[:target_length]

        return compacted

    except Exception as e:
        logger.error(f"Compaction failed: {e}, using truncation")
        return text[:target_length]


def robust_parse_with_llm(
    llm: BaseChatModel,
    text: str,
    output_model: Type[T],
    instruction: str = None,
    fallback_to_llm_extraction: bool = True
) -> T:
    """
    Robust parsing that tries multiple strategies.

    1. First tries structured output (fastest, most reliable)
    2. Falls back to LLM-based extraction if that fails
    3. Has self-healing retry logic
    4. Handles token limits automatically

    Parameters
    ----------
    llm : BaseChatModel
        The language model to use
    text : str
        Text to parse
    output_model : Type[T]
        Target Pydantic model
    instruction : str, optional
        Additional instructions
    fallback_to_llm_extraction : bool
        Whether to try LLM extraction as fallback (default: True)

    Returns
    -------
    T
        Parsed structured output

    Raises
    ------
    RuntimeError
        If all parsing strategies fail
    """
    # Try structured output first
    try:
        return extract_with_structured_output(
            llm=llm,
            text=text,
            output_model=output_model,
            instruction=instruction
        )
    except Exception as e:
        logger.warning(f"Structured output extraction failed: {e}")

        if not fallback_to_llm_extraction:
            raise

        # Fall back to LLM-based extraction
        logger.info("Trying LLM-based extraction fallback...")
        try:
            return extract_with_llm_fallback(
                llm=llm,
                text=text,
                output_model=output_model,
                instruction=instruction
            )
        except Exception as e2:
            raise RuntimeError(
                f"All parsing strategies failed. "
                f"Structured output error: {e}. "
                f"LLM extraction error: {e2}"
            )
