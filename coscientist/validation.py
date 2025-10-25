"""
Early validation for Coscientist framework.

This module ensures all critical configurations are valid BEFORE any expensive
operations begin. Any validation failure should cause immediate catastrophic failure.
"""

import json
import os
import asyncio
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when critical validation fails."""
    pass


def validate_researcher_config(config_path: str) -> dict:
    """
    Validate researcher_config.json format and structure.

    Parameters
    ----------
    config_path : str
        Path to researcher_config.json

    Returns
    -------
    dict
        The validated config

    Raises
    ------
    ValidationError
        If config is invalid or missing required fields
    """
    if not os.path.exists(config_path):
        raise ValidationError(f"researcher_config.json not found at: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in researcher_config.json: {e}")

    # Check required LLM fields
    llm_fields = ["FAST_LLM", "SMART_LLM", "STRATEGIC_LLM"]
    for field in llm_fields:
        if field not in config:
            raise ValidationError(f"Missing required field '{field}' in researcher_config.json")

        # Validate format: provider:model
        llm_value = config[field]
        if not isinstance(llm_value, str) or ":" not in llm_value:
            raise ValidationError(
                f"Invalid format for {field}: '{llm_value}'. "
                f"Expected format: 'provider:model' (e.g., 'google_genai:gemini-1.5-flash')"
            )

        provider, model = llm_value.split(":", 1)
        if not provider or not model:
            raise ValidationError(
                f"Invalid format for {field}: '{llm_value}'. "
                f"Both provider and model must be non-empty."
            )

        logger.info(f"✓ {field}: {provider}:{model}")

    logger.info("✓ researcher_config.json structure is valid")
    return config


async def validate_openai_llm(api_key: str = None) -> None:
    """
    Validate OpenAI LLM access.

    Parameters
    ----------
    api_key : str, optional
        OpenAI API key. If None, reads from OPENAI_API_KEY env var.

    Raises
    ------
    ValidationError
        If OpenAI API is not accessible
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ValidationError(
            "langchain_openai not installed. "
            "Run: uv pip install langchain-openai"
        )

    # Check API key
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValidationError(
            "OPENAI_API_KEY not found in environment. "
            "Set it in your .env file or environment."
        )

    logger.info(f"✓ OPENAI_API_KEY found: {api_key[:10]}...")

    # Test model initialization and simple call
    try:
        model = ChatOpenAI(model="gpt-4o-mini", max_tokens=100, timeout=30)
        response = await model.ainvoke("Say 'test' if you can read this.")
        logger.info(f"✓ OpenAI model accessible. Response: {response.content[:50]}...")
    except Exception as e:
        raise ValidationError(f"OpenAI model test failed: {e}")


async def validate_gemini_llm(api_key: str = None, model_name: str = "gemini-1.5-flash") -> None:
    """
    Validate Google Gemini LLM access.

    Parameters
    ----------
    api_key : str, optional
        Google API key. If None, reads from GOOGLE_API_KEY env var.
    model_name : str
        Gemini model name to test (default: gemini-1.5-flash)

    Raises
    ------
    ValidationError
        If Gemini API is not accessible or model name is invalid
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ValidationError(
            "langchain_google_genai not installed. "
            "Run: uv pip install langchain-google-genai"
        )

    # Check API key
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValidationError(
            "GOOGLE_API_KEY not found in environment. "
            "Set it in your .env file or environment."
        )

    logger.info(f"✓ GOOGLE_API_KEY found: {api_key[:10]}...")

    # Test model initialization and simple call
    try:
        logger.info(f"Testing Gemini model: {model_name}")
        model = ChatGoogleGenerativeAI(
            model=model_name,
            max_tokens=100,
            timeout=30
        )
        response = await model.ainvoke("Say 'test' if you can read this.")
        logger.info(f"✓ Gemini model accessible. Response: {response.content[:50]}...")
    except Exception as e:
        raise ValidationError(
            f"Gemini model '{model_name}' test failed: {e}\n"
            f"Common issue: Model name may be incorrect. "
            f"For Gemini 1.5 Flash, use 'gemini-1.5-flash' (not 'gemini-1.5-flash-latest')"
        )


async def validate_framework_llms() -> None:
    """
    Validate that framework LLM pools are properly configured.

    Raises
    ------
    ValidationError
        If framework LLM pools cannot be loaded
    """
    try:
        from coscientist.framework import _SMARTER_LLM_POOL, _CHEAPER_LLM_POOL

        if not _SMARTER_LLM_POOL:
            raise ValidationError("_SMARTER_LLM_POOL is empty")
        if not _CHEAPER_LLM_POOL:
            raise ValidationError("_CHEAPER_LLM_POOL is empty")

        logger.info("✓ Framework LLM pools loaded:")
        for name, model in _SMARTER_LLM_POOL.items():
            logger.info(f"  - Smarter: {name} ({model.__class__.__name__})")
        for name, model in _CHEAPER_LLM_POOL.items():
            logger.info(f"  - Cheaper: {name} ({model.__class__.__name__})")

    except ImportError as e:
        raise ValidationError(f"Failed to import framework LLM pools: {e}")
    except Exception as e:
        raise ValidationError(f"Framework LLM pool validation failed: {e}")


def validate_gpt_researcher_config_sync(config_path: str) -> None:
    """
    Validate that gpt-researcher can initialize with the config (synchronous).

    Parameters
    ----------
    config_path : str
        Path to researcher_config.json

    Raises
    ------
    ValidationError
        If gpt-researcher cannot initialize or LLM providers are unsupported
    """
    try:
        from gpt_researcher.config.config import Config

        cfg = Config(config_path)

        logger.info(f"✓ GPTResearcher config loaded:")
        logger.info(f"  - FAST_LLM: {cfg.fast_llm_provider}:{cfg.fast_llm_model}")
        logger.info(f"  - SMART_LLM: {cfg.smart_llm_provider}:{cfg.smart_llm_model}")
        logger.info(f"  - STRATEGIC_LLM: {cfg.strategic_llm_provider}:{cfg.strategic_llm_model}")

    except AssertionError as e:
        # gpt-researcher raises AssertionError for unsupported providers
        raise ValidationError(
            f"GPTResearcher config validation failed: {e}\n"
            f"Check that LLM provider names in researcher_config.json match "
            f"gpt-researcher's supported providers."
        )
    except Exception as e:
        raise ValidationError(f"Failed to initialize GPTResearcher config: {e}")


async def validate_gpt_researcher_config(config_path: str) -> None:
    """
    Validate that gpt-researcher can initialize with the config (async wrapper).

    Parameters
    ----------
    config_path : str
        Path to researcher_config.json

    Raises
    ------
    ValidationError
        If gpt-researcher cannot initialize or LLM providers are unsupported
    """
    validate_gpt_researcher_config_sync(config_path)


async def validate_all(
    researcher_config_path: str = None,
    validate_openai: bool = True,
    validate_gemini: bool = False,
    gemini_model: str = "gemini-1.5-flash"
) -> None:
    """
    Run all validation checks. Fails catastrophically on any error.

    Parameters
    ----------
    researcher_config_path : str, optional
        Path to researcher_config.json. If None, uses default location.
    validate_openai : bool
        Whether to validate OpenAI API access (default: True)
    validate_gemini : bool
        Whether to validate Gemini API access (default: False)
    gemini_model : str
        Gemini model name to validate (default: gemini-1.5-flash)

    Raises
    ------
    ValidationError
        If any validation check fails
    """
    logger.info("=" * 80)
    logger.info("COSCIENTIST FRAMEWORK VALIDATION")
    logger.info("=" * 80)

    # Default researcher config path
    if researcher_config_path is None:
        researcher_config_path = os.path.join(
            os.path.dirname(__file__),
            "researcher_config.json"
        )

    # 1. Validate researcher config structure
    logger.info("\n[1/6] Validating researcher_config.json...")
    config = validate_researcher_config(researcher_config_path)

    # 2. Validate gpt-researcher can load it
    logger.info("\n[2/6] Validating GPTResearcher initialization...")
    await validate_gpt_researcher_config(researcher_config_path)

    # 3. Validate framework LLM pools
    logger.info("\n[3/6] Validating framework LLM pools...")
    await validate_framework_llms()

    # 4. Validate OpenAI (optional)
    if validate_openai:
        logger.info("\n[4/6] Validating OpenAI API access...")
        await validate_openai_llm()
    else:
        logger.info("\n[4/6] Skipping OpenAI validation")

    # 5. Validate Gemini (optional)
    if validate_gemini:
        logger.info("\n[5/6] Validating Gemini API access...")
        await validate_gemini_llm(model_name=gemini_model)
    else:
        logger.info("\n[5/6] Skipping Gemini validation")

    # 6. Detect which LLMs are actually configured
    logger.info("\n[6/6] Detecting configured LLM providers...")
    llm_providers = set()
    for field in ["FAST_LLM", "SMART_LLM", "STRATEGIC_LLM"]:
        provider = config[field].split(":")[0]
        llm_providers.add(provider)

    logger.info(f"Configured providers: {', '.join(llm_providers)}")

    # Validate the providers that are actually configured
    if "openai" in llm_providers and not validate_openai:
        logger.warning(
            "⚠️  OpenAI is configured but validation was skipped. "
            "Set validate_openai=True to test."
        )

    if "google_genai" in llm_providers and not validate_gemini:
        logger.warning(
            "⚠️  Google Gemini is configured but validation was skipped. "
            "Set validate_gemini=True to test."
        )

    logger.info("\n" + "=" * 80)
    logger.info("✅ ALL VALIDATION CHECKS PASSED")
    logger.info("=" * 80 + "\n")


def validate_all_sync(
    researcher_config_path: str = None,
    validate_openai: bool = True,
    validate_gemini: bool = False,
    gemini_model: str = "gemini-1.5-flash"
) -> None:
    """
    Synchronous wrapper for validate_all().

    Parameters
    ----------
    researcher_config_path : str, optional
        Path to researcher_config.json
    validate_openai : bool
        Whether to validate OpenAI API access
    validate_gemini : bool
        Whether to validate Gemini API access
    gemini_model : str
        Gemini model name to validate

    Raises
    ------
    ValidationError
        If any validation check fails
    """
    asyncio.run(validate_all(
        researcher_config_path=researcher_config_path,
        validate_openai=validate_openai,
        validate_gemini=validate_gemini,
        gemini_model=gemini_model
    ))
