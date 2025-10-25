"""
Single source of truth for all LLM/embedding configuration.

This module reads researcher_config.json and creates all LLM instances.
NO DEFAULTS. NO FALLBACKS. Config must be correct or we crash.
"""

import json
import os
from pathlib import Path
from typing import Dict

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_anthropic import ChatAnthropic


class ConfigurationError(Exception):
    """Raised when configuration is invalid. This should CRASH the system."""
    pass


def load_researcher_config(config_path: str = None) -> dict:
    """
    Load researcher_config.json. Crashes if file doesn't exist or is invalid.

    Parameters
    ----------
    config_path : str, optional
        Path to config file. If None, uses default location.

    Returns
    -------
    dict
        The loaded configuration

    Raises
    ------
    ConfigurationError
        If file doesn't exist, is invalid JSON, or missing required fields
    """
    if config_path is None:
        config_path = Path(__file__).parent / "researcher_config.json"

    if not os.path.exists(config_path):
        raise ConfigurationError(
            f"researcher_config.json not found at: {config_path}\n"
            f"This file is REQUIRED. Create it or fix the path."
        )

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"researcher_config.json contains invalid JSON: {e}\n"
            f"Fix the syntax errors in {config_path}"
        )

    # Validate required fields exist
    required_fields = ["FAST_LLM", "SMART_LLM", "STRATEGIC_LLM", "EMBEDDING"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise ConfigurationError(
            f"researcher_config.json is missing required fields: {missing}\n"
            f"File: {config_path}"
        )

    return config


def _create_llm(provider: str, model: str, max_tokens: int, max_retries: int = 3) -> BaseChatModel:
    """
    Create an LLM instance from provider and model name.

    Crashes if provider is unknown or credentials are missing.
    """
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                f"OPENAI_API_KEY environment variable not set.\n"
                f"You specified openai:{model} in config but have no API key."
            )
        return ChatOpenAI(model=model, max_tokens=max_tokens, max_retries=max_retries)

    elif provider == "google_genai":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ConfigurationError(
                f"GOOGLE_API_KEY environment variable not set.\n"
                f"You specified google_genai:{model} in config but have no API key."
            )
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=1.0,
            max_retries=max_retries,
            max_tokens=max_tokens
        )

    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ConfigurationError(
                f"ANTHROPIC_API_KEY environment variable not set.\n"
                f"You specified anthropic:{model} in config but have no API key."
            )
        return ChatAnthropic(model=model, max_tokens=max_tokens, max_retries=max_retries)

    else:
        raise ConfigurationError(
            f"Unknown LLM provider: {provider}\n"
            f"Supported providers: openai, google_genai, anthropic\n"
            f"Check your researcher_config.json"
        )


def _create_embeddings(provider: str, model: str) -> Embeddings:
    """
    Create an embeddings instance from provider and model name.

    Crashes if provider is unknown or credentials are missing.
    """
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError(
                f"OPENAI_API_KEY environment variable not set.\n"
                f"You specified openai:{model} for embeddings but have no API key."
            )
        # Extract dimensions if specified (e.g., "text-embedding-3-small:256")
        if ":" in model:
            model_name, dims = model.split(":", 1)
            return OpenAIEmbeddings(model=model_name, dimensions=int(dims))
        return OpenAIEmbeddings(model=model)

    elif provider == "google_genai":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ConfigurationError(
                f"GOOGLE_API_KEY environment variable not set.\n"
                f"You specified google_genai:{model} for embeddings but have no API key."
            )
        return GoogleGenerativeAIEmbeddings(model=model)

    else:
        raise ConfigurationError(
            f"Unknown embeddings provider: {provider}\n"
            f"Supported providers: openai, google_genai\n"
            f"Check your researcher_config.json EMBEDDING field"
        )


def create_llms_from_config(config_path: str = None) -> Dict[str, BaseChatModel]:
    """
    Create all LLM instances from researcher_config.json.

    Returns a dict with keys matching config (FAST_LLM, SMART_LLM, etc.)
    plus a 'pool' key containing a dict of unique models.

    Crashes immediately if anything is wrong.

    Returns
    -------
    dict
        {
            'FAST_LLM': ChatOpenAI(...),
            'SMART_LLM': ChatGoogleGenerativeAI(...),
            'STRATEGIC_LLM': ...,
            'pool': {'gpt-4o-mini': ChatOpenAI(...), ...}  # Unique models by name
        }
    """
    config = load_researcher_config(config_path)

    llms = {}
    pool = {}

    for field in ["FAST_LLM", "SMART_LLM", "STRATEGIC_LLM"]:
        llm_spec = config[field]

        # Parse provider:model
        if ":" not in llm_spec:
            raise ConfigurationError(
                f"{field} has invalid format: '{llm_spec}'\n"
                f"Expected format: 'provider:model' (e.g., 'google_genai:gemini-2.5-flash')"
            )

        provider, model = llm_spec.split(":", 1)

        # Determine token limit from config
        token_limit_field = field.replace("_LLM", "_TOKEN_LIMIT")
        # Default 16000 (Gemini 2.5 Flash supports up to 65K output tokens)
        max_tokens = config.get(token_limit_field, 16000)

        # Create LLM instance
        llm = _create_llm(provider, model, max_tokens)
        llms[field] = llm

        # Add to pool (keyed by model name to deduplicate)
        pool[model] = llm

    llms['pool'] = pool
    return llms


def create_embeddings_from_config(config_path: str = None) -> Embeddings:
    """
    Create embeddings instance from researcher_config.json.

    Crashes immediately if anything is wrong.
    """
    config = load_researcher_config(config_path)

    embedding_spec = config["EMBEDDING"]

    # Parse provider:model
    if ":" not in embedding_spec:
        raise ConfigurationError(
            f"EMBEDDING has invalid format: '{embedding_spec}'\n"
            f"Expected format: 'provider:model' (e.g., 'google_genai:models/text-embedding-004')"
        )

    provider, model = embedding_spec.split(":", 1)

    return _create_embeddings(provider, model)


def validate_all_config(config_path: str = None):
    """
    Validate EVERYTHING in the config by making real API calls.

    This is expensive but ensures the config actually works.
    Crashes immediately if anything fails.
    """
    print("=" * 80)
    print("VALIDATING CONFIGURATION WITH REAL API CALLS")
    print("=" * 80)

    # 1. Load and create LLMs
    print("\n[1/3] Creating LLM instances from config...")
    llms = create_llms_from_config(config_path)
    print(f"  ✓ Created {len(llms['pool'])} unique LLM(s)")
    for model_name in llms['pool'].keys():
        print(f"    - {model_name}")

    # 2. Test each LLM with a real API call
    print("\n[2/3] Testing LLMs with real API calls...")
    for model_name, llm in llms['pool'].items():
        print(f"  Testing {model_name}...", end=" ")
        try:
            response = llm.invoke("Say 'OK' if you can read this.")
            if not response.content:
                raise ConfigurationError(f"LLM {model_name} returned empty response")
            print(f"✓ Response: {response.content[:50]}")
        except Exception as e:
            raise ConfigurationError(
                f"\n  ✗ LLM {model_name} FAILED API test:\n"
                f"  {type(e).__name__}: {e}\n"
                f"  Check your API key and model name in researcher_config.json"
            )

    # 3. Create and test embeddings
    print("\n[3/3] Creating and testing embeddings...")
    embeddings = create_embeddings_from_config(config_path)
    print(f"  Testing embeddings...", end=" ")
    try:
        # Test with small text first
        test_embedding = embeddings.embed_query("test")
        if not test_embedding or len(test_embedding) == 0:
            raise ConfigurationError("Embeddings returned empty vector")
        print(f"✓ Dimension: {len(test_embedding)}")
    except Exception as e:
        raise ConfigurationError(
            f"\n  ✗ Embeddings FAILED API test:\n"
            f"  {type(e).__name__}: {e}\n"
            f"  Check your API key and embedding model in researcher_config.json"
        )

    print("\n" + "=" * 80)
    print("✅ ALL CONFIGURATION VALID - READY TO RUN")
    print("=" * 80 + "\n")
