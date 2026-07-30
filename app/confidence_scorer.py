from dataclasses import dataclass, field


# Weights are hand-set and explainable, not learned — each reflects how much
# an independent, external signal should count relative to the others.
# NOTE: these are a reasonable starting point, not a proven-optimal split —
# Milestone 5's eval suite is what would let you actually tune these against
# labeled data instead of intuition.
SIGNAL_WEIGHTS = {
    "syntax_valid": 0.10,       # cheap, deterministic — a low bar, low weight
    "back_translation": 0.30,   # independent check that SQL matches intent
    "sanity_check": 0.25,       # independent check that DATA looks plausible
    "multi_query_agreement": 0.25,  # independent second generation converging
    "schema_coverage": 0.10,    # used the tables retrieval expected
}


@dataclass
class ConfidenceBreakdown:
    final_score: float
    signals: dict = field(default_factory=dict)
    flagged_issues: list[str] = field(default_factory=list)


def compute_confidence(
    syntax_valid: bool,
    back_translation_alignment: float,
    sanity_passed: bool,
    sanity_issues: list[str],
    multi_query_agreement: float,
    schema_coverage: float,
) -> ConfidenceBreakdown:
    signals = {
        "syntax_valid": 1.0 if syntax_valid else 0.0,
        "back_translation": back_translation_alignment,
        "sanity_check": 1.0 if sanity_passed else 0.3,  # not zeroed — sanity issues are a flag, not proof of wrongness
        "multi_query_agreement": multi_query_agreement,
        "schema_coverage": schema_coverage,
    }

    final_score = sum(signals[key] * weight for key, weight in SIGNAL_WEIGHTS.items())

    flagged_issues = list(sanity_issues)
    if back_translation_alignment < 0.5:
        flagged_issues.append(
            f"Back-translation alignment is low ({back_translation_alignment:.2f}) — "
            f"the generated SQL may not answer the question as asked."
        )
    if multi_query_agreement < 0.5:
        flagged_issues.append(
            f"Independent second query generation disagreed with the first "
            f"(agreement={multi_query_agreement:.2f}) — results may be unreliable."
        )

    return ConfidenceBreakdown(
        final_score=round(final_score, 3),
        signals=signals,
        flagged_issues=flagged_issues,
    )


def compute_schema_coverage(tables_used: list[str], expected_tables: list[str]) -> float:
    """How well the tables actually used match the tables retrieval expected —
    reuses Milestone 2's schema filter output as ground truth for 'expected'."""
    if not expected_tables:
        return 1.0
    used_set = set(tables_used)
    expected_set = set(expected_tables)
    overlap = len(used_set & expected_set)
    return overlap / len(expected_set)