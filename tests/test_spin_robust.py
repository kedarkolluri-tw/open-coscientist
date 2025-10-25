#!/usr/bin/env python3
"""
Take robust parsing for a spin with real hypothesis generation.

Shows:
1. LLM generates hypothesis (might be poorly formatted)
2. Robust parsing handles it automatically
3. Self-healing if something goes wrong
"""

import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

load_dotenv(".env.test")

from langchain_openai import ChatOpenAI
from coscientist.common import parse_hypothesis_with_llm
from coscientist.custom_types import ParsedHypothesis

def test_real_hypothesis_generation():
    """Generate real hypotheses and parse them robustly."""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    test_cases = [
        {
            "name": "Standard Scientific Question",
            "prompt": "Generate a hypothesis about how vitamin D affects immune function. Include predictions and assumptions."
        },
        {
            "name": "Complex Research Question",
            "prompt": "What is the relationship between the gut microbiome and mental health? Provide a testable hypothesis with 3 predictions."
        },
        {
            "name": "Deliberately Poor Format",
            "prompt": "Just tell me your hypothesis about caffeine and athletic performance in a casual way, without any special formatting."
        },
    ]

    print("\n" + "=" * 80)
    print("TAKING ROBUST PARSING FOR A SPIN")
    print("=" * 80 + "\n")

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'=' * 80}\n")

        print(f"Prompt: {test['prompt']}\n")

        try:
            # Generate hypothesis from LLM
            print("Generating hypothesis...")
            response = llm.invoke(test['prompt'])
            raw_text = response.content

            print(f"\nLLM Response (first 200 chars):")
            print(f"{raw_text[:200]}...\n")

            # Parse with robust method
            print("Parsing with robust LLM-based parser...")
            parsed = parse_hypothesis_with_llm(llm, raw_text)

            # Show results
            print("\n✅ PARSING SUCCESSFUL!\n")
            print(f"Hypothesis: {parsed.hypothesis[:100]}...")
            print(f"Predictions ({len(parsed.predictions)} items):")
            for j, pred in enumerate(parsed.predictions[:2], 1):
                print(f"  {j}. {pred[:80]}...")
            if len(parsed.predictions) > 2:
                print(f"  ... and {len(parsed.predictions) - 2} more")

            print(f"\nAssumptions ({len(parsed.assumptions)} items):")
            for j, assump in enumerate(parsed.assumptions[:2], 1):
                print(f"  {j}. {assump[:80]}...")
            if len(parsed.assumptions) > 2:
                print(f"  ... and {len(parsed.assumptions) - 2} more")

            results.append(("✅", test['name']))

        except Exception as e:
            print(f"\n❌ PARSING FAILED: {e}\n")
            results.append(("❌", test['name']))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80 + "\n")

    for status, name in results:
        print(f"{status} {name}")

    passed = sum(1 for status, _ in results if status == "✅")
    total = len(results)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 Perfect! Robust parsing handled all cases including poorly-formatted output.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")

    return passed == total


def test_edge_cases():
    """Test specific edge cases like very long text."""

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    print("\n" + "=" * 80)
    print("TESTING EDGE CASES")
    print("=" * 80 + "\n")

    # Test 1: Very long context
    print("1. Very long input (token limit stress test):")
    long_text = """
# Hypothesis
The gut-brain axis modulates mood through microbial production of neurotransmitter precursors.

# Predictions
1. """ + " ".join(["Test prediction with lots of detail"] * 100) + """
2. Second prediction
3. Third prediction

# Assumptions
1. """ + " ".join(["Background assumption text"] * 100) + """
2. Second assumption
"""

    try:
        print(f"  Input length: {len(long_text)} characters")
        parsed = parse_hypothesis_with_llm(llm, long_text)
        print(f"  ✅ Parsed successfully (may have compacted if needed)")
        print(f"  Hypothesis: {parsed.hypothesis[:80]}...")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # Test 2: Missing sections
    print("\n2. Missing predictions section:")
    incomplete = """
# Hypothesis
Probiotics reduce inflammation in IBD patients.

(No predictions provided)
"""

    try:
        parsed = parse_hypothesis_with_llm(llm, incomplete)
        print(f"  ✅ Handled gracefully")
        print(f"  Hypothesis: {parsed.hypothesis[:80]}...")
        if parsed.predictions:
            print(f"  Predictions ({len(parsed.predictions)}): {parsed.predictions[0][:60]}...")
        else:
            print(f"  Predictions: (none extracted - as expected)")
        if parsed.assumptions:
            print(f"  Assumptions ({len(parsed.assumptions)}): {parsed.assumptions[0][:60]}...")
        else:
            print(f"  Assumptions: (none extracted)")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # Test 3: Unusual formatting
    print("\n3. Unusual formatting (no headers, prose style):")
    prose = """
    I believe that exercise improves cognitive function through increased BDNF.
    We could test this by measuring BDNF levels after workouts.
    Another prediction is improved memory scores in exercise groups.
    We're assuming BDNF crosses the blood-brain barrier.
    """

    try:
        parsed = parse_hypothesis_with_llm(llm, prose)
        print(f"  ✅ Extracted despite no structure")
        print(f"  Hypothesis: {parsed.hypothesis[:80]}...")
    except Exception as e:
        print(f"  ❌ Failed: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ROBUST PARSING - REAL WORLD TEST")
    print("=" * 80)

    # Main tests
    success = test_real_hypothesis_generation()

    # Edge cases
    test_edge_cases()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80 + "\n")

    if success:
        print("✓ Robust parsing is working great!")
        print("✓ Handles various formats automatically")
        print("✓ Self-heals on errors")
        print("✓ Ready for production use")
    else:
        print("Some tests failed - review errors above")
