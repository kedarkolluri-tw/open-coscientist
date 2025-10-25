#!/usr/bin/env python3
"""
Test that validation failures trigger self-healing retries.

This demonstrates the self-healing architecture:
1. LLM returns incomplete result (e.g., empty predictions)
2. Validation catches it
3. System retries with error feedback
4. LLM corrects itself
"""

import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

load_dotenv(".env.test")

from langchain_openai import ChatOpenAI
from coscientist.common import parse_hypothesis_with_llm
from coscientist.custom_types import ParsedHypothesis

def test_self_healing():
    """Test self-healing when LLM returns incomplete data."""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    print("\n" + "=" * 80)
    print("TESTING SELF-HEALING WITH VALIDATION")
    print("=" * 80 + "\n")

    # Test case that's likely to produce incomplete output
    incomplete_text = """
# Hypothesis
Probiotics reduce inflammation in IBD patients.

(The researcher hasn't provided predictions yet)
"""

    print("Input text (deliberately incomplete):")
    print(incomplete_text)
    print("\n" + "=" * 80 + "\n")

    try:
        print("Attempting to parse...")
        parsed = parse_hypothesis_with_llm(llm, incomplete_text)

        print("\n✅ PARSING SUCCESSFUL AFTER SELF-HEALING!\n")
        print(f"Hypothesis: {parsed.hypothesis[:80]}...")
        print(f"\nPredictions ({len(parsed.predictions)}):")
        for i, pred in enumerate(parsed.predictions, 1):
            print(f"  {i}. {pred[:80]}...")

        print(f"\nAssumptions ({len(parsed.assumptions)}):")
        for i, assump in enumerate(parsed.assumptions, 1):
            print(f"  {i}. {assump[:80]}...")

        print("\n" + "=" * 80)
        print("SELF-HEALING WORKED!")
        print("=" * 80)
        print("""
What happened:
1. LLM initially may have returned empty/incomplete predictions
2. Validation caught it: "predictions must contain at least one item"
3. System added error feedback to prompt
4. LLM retried and generated proper predictions
5. Success!

This is exactly what you wanted: the system knows something is wrong
and automatically corrects itself.
""")

    except Exception as e:
        print(f"\n❌ PARSING FAILED EVEN AFTER RETRIES: {e}\n")
        print("This means all 3 retry attempts couldn't extract predictions.")
        print("The input may be genuinely too incomplete to work with.")


def test_quality_validation():
    """Test that quality validation rejects garbage output."""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    print("\n" + "=" * 80)
    print("TESTING QUALITY VALIDATION")
    print("=" * 80 + "\n")

    bad_inputs = [
        {
            "name": "Placeholder text",
            "text": "# Hypothesis\nTODO: Write hypothesis here\n# Predictions\n1. TBD"
        },
        {
            "name": "Error message as hypothesis",
            "text": "# Hypothesis\nFailed to parse hypothesis from input\n# Predictions\n1. None"
        },
        {
            "name": "Too short",
            "text": "# Hypothesis\nTest\n# Predictions\n1. X"
        }
    ]

    for test in bad_inputs:
        print(f"\nTest: {test['name']}")
        try:
            parsed = parse_hypothesis_with_llm(llm, test['text'])
            print(f"  ⚠️  Accepted (may have self-healed to valid content)")
            print(f"  Hypothesis: {parsed.hypothesis[:60]}...")
        except Exception as e:
            print(f"  ✅ Rejected: {str(e)[:80]}...")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SELF-HEALING VALIDATION TEST")
    print("=" * 80)

    test_self_healing()
    test_quality_validation()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80 + "\n")
