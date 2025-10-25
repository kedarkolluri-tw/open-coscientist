#!/usr/bin/env python3
"""
Smoke test to validate LLM configurations before running full research.
Tests all configured LLM providers to ensure they're accessible and working.
"""

import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.test")

def test_researcher_config():
    """Test that researcher_config.json is valid and models are properly formatted."""
    print("🔍 Testing researcher_config.json...")

    with open("coscientist/researcher_config.json", "r") as f:
        config = json.load(f)

    # Check required LLM fields
    llm_fields = ["FAST_LLM", "SMART_LLM", "STRATEGIC_LLM"]
    for field in llm_fields:
        if field not in config:
            print(f"❌ Missing {field} in config")
            return False

        # Validate format: provider:model
        llm_value = config[field]
        if ":" not in llm_value:
            print(f"❌ Invalid format for {field}: {llm_value} (expected provider:model)")
            return False

        provider, model = llm_value.split(":", 1)
        print(f"✓ {field}: {provider}:{model}")

    print("✅ researcher_config.json is valid\n")
    return True


def test_gpt_researcher_llm():
    """Test that gpt-researcher can initialize with configured LLMs."""
    print("🔍 Testing GPTResearcher LLM initialization...")

    try:
        from gpt_researcher.config.config import Config
        import os

        config_path = os.path.join(os.path.dirname(__file__), "coscientist/researcher_config.json")
        cfg = Config(config_path)

        print(f"✓ FAST_LLM: {cfg.fast_llm_provider}:{cfg.fast_llm_model}")
        print(f"✓ SMART_LLM: {cfg.smart_llm_provider}:{cfg.smart_llm_model}")
        print(f"✓ STRATEGIC_LLM: {cfg.strategic_llm_provider}:{cfg.strategic_llm_model}")

        print("✅ GPTResearcher LLM config loaded successfully\n")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize GPTResearcher config: {e}\n")
        return False


async def test_gemini_model():
    """Test that Gemini models are accessible."""
    print("🔍 Testing Gemini model access...")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        import os

        # Check API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return False

        print(f"✓ GOOGLE_API_KEY found: {api_key[:10]}...")

        # Test model initialization and simple call
        print("Testing gemini-1.5-flash-latest...")
        model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            max_tokens=100
        )

        response = await model.ainvoke("Say 'test successful' if you can read this.")
        print(f"✓ Model response: {response.content[:50]}...")

        print("✅ Gemini model is accessible\n")
        return True
    except Exception as e:
        print(f"❌ Gemini model test failed: {e}\n")
        return False


async def test_openai_model():
    """Test that OpenAI models are accessible."""
    print("🔍 Testing OpenAI model access...")

    try:
        from langchain_openai import ChatOpenAI
        import os

        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False

        print(f"✓ OPENAI_API_KEY found: {api_key[:10]}...")

        # Test model initialization and simple call
        print("Testing gpt-4o-mini...")
        model = ChatOpenAI(model="gpt-4o-mini", max_tokens=100)

        response = await model.ainvoke("Say 'test successful' if you can read this.")
        print(f"✓ Model response: {response.content[:50]}...")

        print("✅ OpenAI model is accessible\n")
        return True
    except Exception as e:
        print(f"❌ OpenAI model test failed: {e}\n")
        return False


async def test_framework_llms():
    """Test that framework LLMs are properly configured."""
    print("🔍 Testing CoscientistFramework LLM pools...")

    try:
        from coscientist.framework import _SMARTER_LLM_POOL, _CHEAPER_LLM_POOL

        print("Smarter LLM pool:")
        for name, model in _SMARTER_LLM_POOL.items():
            print(f"  ✓ {name}: {model.__class__.__name__}")

        print("Cheaper LLM pool:")
        for name, model in _CHEAPER_LLM_POOL.items():
            print(f"  ✓ {name}: {model.__class__.__name__}")

        print("✅ Framework LLM pools are valid\n")
        return True
    except Exception as e:
        print(f"❌ Framework LLM pool test failed: {e}\n")
        return False


async def main():
    """Run all smoke tests."""
    print("=" * 80)
    print("LLM Configuration Smoke Tests")
    print("=" * 80 + "\n")

    results = []

    # Synchronous tests
    results.append(("Researcher Config", test_researcher_config()))
    results.append(("GPTResearcher Init", test_gpt_researcher_llm()))
    results.append(("Framework LLMs", await test_framework_llms()))

    # Async model tests
    results.append(("OpenAI Model", await test_openai_model()))
    results.append(("Gemini Model", await test_gemini_model()))

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! LLM configuration is valid.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Fix configuration before running research.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
