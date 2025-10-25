import uuid

from pydantic import BaseModel, Field, field_validator


class ParsedHypothesis(BaseModel):
    """Structured output for parsed hypothesis."""

    uid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the hypothesis",
    )
    hypothesis: str = Field(
        description="The main hypothesis statement. Must be a clear, testable statement.",
        min_length=10
    )
    predictions: list[str] = Field(
        description="A list of falsifiable predictions that could be tested to disprove the hypothesis. Must include at least one prediction.",
        min_length=1
    )
    assumptions: list[str] = Field(
        description="A list of assumptions that are implicit or explicit in the hypothesis. Must include at least one assumption.",
        min_length=1
    )
    parent_uid: str | None = Field(
        default=None,
        description="The unique identifier of the parent hypothesis, if applicable",
    )

    @field_validator('predictions', 'assumptions')
    @classmethod
    def validate_non_empty_items(cls, v: list[str], info) -> list[str]:
        """Ensure list items are not empty strings."""
        if not v:
            raise ValueError(f"{info.field_name} must contain at least one item")

        # Check for empty strings
        non_empty = [item for item in v if item.strip()]
        if not non_empty:
            raise ValueError(f"{info.field_name} contains only empty strings")

        # Warn if we filtered out empty items
        if len(non_empty) < len(v):
            return non_empty

        return v

    @field_validator('hypothesis')
    @classmethod
    def validate_hypothesis_quality(cls, v: str) -> str:
        """Ensure hypothesis is substantial and not a placeholder."""
        if not v or not v.strip():
            raise ValueError("Hypothesis cannot be empty")

        v = v.strip()

        # Check for common placeholder patterns
        placeholder_phrases = [
            "failed to parse",
            "could not extract",
            "missing",
            "not provided",
            "todo",
            "tbd",
            "to be determined"
        ]

        v_lower = v.lower()
        for phrase in placeholder_phrases:
            if phrase in v_lower:
                raise ValueError(
                    f"Hypothesis appears to be a placeholder or error message: '{v[:100]}...'"
                )

        return v


class ReviewedHypothesis(ParsedHypothesis):
    """Structured output for reviewed hypothesis."""

    causal_reasoning: str = Field(description="The causal reasoning for the hypothesis")
    assumption_research_results: dict[str, str] = Field(
        description="A dictionary of assumption research results"
    )
    verification_result: str = Field(
        description="The result of the deep verification process"
    )


class RankingMatchResult(BaseModel):
    """Result of a match between two hypotheses."""

    uid1: str = Field(description="Unique identifier for the first hypothesis")
    uid2: str = Field(description="Unique identifier for the second hypothesis")
    winner: int = Field(description="The winner of the match (1 or 2)")
    debate: str = Field(description="The debate between the two hypotheses")
