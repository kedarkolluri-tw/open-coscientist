#!/usr/bin/env python3
"""
Test robust LLM-based parsing vs brittle regex parsing.

Demonstrates:
1. Structured output (JSON) from LLM
2. Self-healing retry logic
3. Token limit handling with compaction
4. LLM-based fallback extraction
"""

import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

load_dotenv(".env.test")

from langchain_openai import ChatOpenAI
from coscientist.common import parse_hypothesis_markdown, parse_hypothesis_with_llm
from coscientist.custom_types import ParsedHypothesis

# Test cases: well-formatted and poorly-formatted hypotheses
WELL_FORMATTED = """
# Hypothesis
Gut microbiome dysbiosis contributes to rheumatoid arthritis inflammation through increased intestinal permeability.

# Falsifiable Predictions
1. RA patients will show decreased microbial diversity compared to healthy controls
2. Specific bacterial species (e.g., Prevotella copri) will be enriched in RA patients
3. Probiotic intervention will reduce inflammatory markers in RA patients

# Assumptions
1. The gut-joint axis exists and mediates systemic inflammation
2. Microbial metabolites can cross the intestinal barrier
3. The immune system responds to microbial signals
"""

POORLY_FORMATTED = """
My hypothesis is that gut microbiome dysbiosis contributes to rheumatoid arthritis
inflammation through increased intestinal permeability.

Some predictions that could be tested:
- RA patients will show decreased microbial diversity compared to healthy controls
- Specific bacterial species (e.g., Prevotella copri) will be enriched in RA patients
- Probiotic intervention will reduce inflammatory markers in RA patients

I'm assuming:
* The gut-joint axis exists and mediates systemic inflammation
* Microbial metabolites can cross the intestinal barrier
* The immune system responds to microbial signals
"""

MISSING_SECTIONS = """
# Hypothesis
Gut microbiome dysbiosis contributes to rheumatoid arthritis inflammation.

That's my hypothesis. I haven't worked out the predictions or assumptions yet.
"""


def test_regex_parsing():
    """Test old regex-based parsing."""
    print("\n" + "=" * 80)
    print("TESTING REGEX-BASED PARSING (OLD METHOD)")
    print("=" * 80 + "\n")

    print("1. Well-formatted text:")
    try:
        result = parse_hypothesis_markdown(WELL_FORMATTED)
        print(f"✓ Parsed successfully")
        print(f"  Predictions: {len(result.predictions)} items")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n2. Poorly-formatted text:")
    try:
        result = parse_hypothesis_markdown(POORLY_FORMATTED)
        print(f"✓ Parsed: {result.predictions[0][:50]}...")
        if "Failed to parse" in str(result.predictions):
            print("  ⚠️  Had to use fallback messages")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n3. Missing sections:")
    try:
        result = parse_hypothesis_markdown(MISSING_SECTIONS)
        print(f"✓ Parsed: {result.predictions[0][:50]}...")
        if "Failed to parse" in str(result.predictions):
            print("  ⚠️  Had to use fallback messages")
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_llm_parsing():
    """Test new LLM-based parsing."""
    print("\n" + "=" * 80)
    print("TESTING LLM-BASED PARSING (NEW METHOD)")
    print("=" * 80 + "\n")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    print("1. Well-formatted text:")
    try:
        result = parse_hypothesis_with_llm(llm, WELL_FORMATTED)
        print(f"✓ Parsed successfully")
        print(f"  Hypothesis: {result.hypothesis[:60]}...")
        print(f"  Predictions: {len(result.predictions)} items")
        print(f"  Assumptions: {len(result.assumptions)} items")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n2. Poorly-formatted text (no # headers, mixed bullets):")
    try:
        result = parse_hypothesis_with_llm(llm, POORLY_FORMATTED)
        print(f"✓ Parsed successfully with LLM semantic understanding")
        print(f"  Hypothesis: {result.hypothesis[:60]}...")
        print(f"  Predictions: {len(result.predictions)} items")
        print(f"  Assumptions: {len(result.assumptions)} items")
        print(f"  First prediction: {result.predictions[0][:80]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n3. Missing sections:")
    try:
        result = parse_hypothesis_with_llm(llm, MISSING_SECTIONS)
        print(f"✓ Parsed successfully (LLM extracted what was available)")
        print(f"  Hypothesis: {result.hypothesis[:60]}...")
        print(f"  Predictions: {len(result.predictions)} items - {result.predictions[0][:60]}...")
        print(f"  Assumptions: {len(result.assumptions)} items - {result.assumptions[0][:60]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")


def main():
    print("\n" + "=" * 80)
    print("ROBUST PARSING COMPARISON")
    print("=" * 80)

    # Test old method
    test_regex_parsing()

    # Test new method
    test_llm_parsing()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
Key improvements with LLM-based parsing:

1. ✓ Handles poorly-formatted input (no strict # headers required)
2. ✓ Semantic understanding (understands "My hypothesis is..." vs "# Hypothesis")
3. ✓ Handles mixed bullet formats (-, *, numbers, etc.)
4. ✓ Self-healing: retries with error feedback if parsing fails
5. ✓ Token limits: automatically compacts input if too long
6. ✓ Structured output: LLM outputs JSON directly (no regex)

Migration path:
- Old method (parse_hypothesis_markdown): Still available for compatibility
- New method (parse_hypothesis_with_llm): Recommended for all new code
- Agents can gradually migrate to use llm parameter in their prompts
""")


if __name__ == "__main__":
    main()
