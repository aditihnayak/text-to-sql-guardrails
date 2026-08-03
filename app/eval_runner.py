import json
import time

from groq import RateLimitError

from db import engine
from schema_introspection import introspect_schema
from schema_filter import filter_relevant_tables
from prompt_constructor import build_prompt
from llm_client import get_llm_client
from guardrail import apply_guardrails
from query_executor import execute_readonly
from back_translation import back_translate, score_alignment
from sanity_checker import check_result_sanity
from multi_query_validator import build_alternative_prompt, compare_results
from confidence_scorer import compute_confidence, compute_schema_coverage
from eval_comparators import exact_match, execution_match
from golden_dataset import GOLDEN_DATASET, GoldenExample

LOW_CONFIDENCE_THRESHOLD = 0.5


def run_pipeline(question: str, llm_client):
    """The same pipeline as /v1/query, extracted so both the API and the
    eval runner call one shared implementation instead of duplicating logic."""
    tables = introspect_schema(engine)
    relevant_tables = filter_relevant_tables(question, tables)
    expected_table_names = [t.table.name for t in relevant_tables]
    prompt = build_prompt(question, relevant_tables)

    generation = llm_client.generate_sql(prompt)
    guardrail_result = apply_guardrails(generation.sql)

    if not guardrail_result.allowed:
        return {
            "generated_sql": generation.sql,
            "executed": False,
            "blocked_reason": guardrail_result.reason,
            "confidence": 0.0,
            "flagged_issues": [f"Blocked: {guardrail_result.reason}"],
        }

    execution = execute_readonly(engine, guardrail_result.sql)

    if execution.error:
        return {
            "generated_sql": guardrail_result.sql,
            "executed": False,
            "error": execution.error,
            "confidence": 0.0,
            "flagged_issues": [f"Execution error: {execution.error}"],
        }

    back_translated = back_translate(guardrail_result.sql, llm_client)
    alignment_score = score_alignment(question, back_translated)

    sanity_result = check_result_sanity(execution.rows)

    alt_prompt = build_alternative_prompt(prompt)
    alt_generation = llm_client.generate_sql(alt_prompt)
    alt_guardrail = apply_guardrails(alt_generation.sql)

    if alt_guardrail.allowed:
        alt_execution = execute_readonly(engine, alt_guardrail.sql)
        agreement = (
            compare_results(execution.rows, alt_execution.rows)
            if not alt_execution.error
            else 0.0
        )
    else:
        agreement = 0.0

    schema_coverage = compute_schema_coverage(
        generation.tables_used,
        expected_table_names,
    )

    confidence = compute_confidence(
        syntax_valid=True,
        back_translation_alignment=alignment_score,
        sanity_passed=sanity_result.passed,
        sanity_issues=sanity_result.issues,
        multi_query_agreement=agreement,
        schema_coverage=schema_coverage,
    )

    return {
        "generated_sql": guardrail_result.sql,
        "executed": True,
        "rows": execution.rows,
        "confidence": confidence.final_score,
        "flagged_issues": confidence.flagged_issues,
    }


def grade_example(example: GoldenExample, result: dict) -> dict:
    grade = {
        "question": example.question,
        "category": example.category,
    }

    if not example.is_answerable:
        correctly_handled = (
            (not result["executed"])
            or (result["confidence"] < LOW_CONFIDENCE_THRESHOLD)
        )

        grade["correctly_flagged_unanswerable"] = correctly_handled
        grade["confidence"] = result["confidence"]
        return grade

    if not result["executed"]:
        grade.update(
            exact_match=False,
            execution_match_score=0.0,
            confidence=result["confidence"],
        )
        return grade

    grade["exact_match"] = exact_match(
        result["generated_sql"],
        example.golden_sql,
    )

    grade["execution_match_score"] = execution_match(
        engine,
        result["generated_sql"],
        example.golden_sql,
    )

    grade["confidence"] = result["confidence"]

    return grade


def run_eval_suite():
    llm_client = get_llm_client()
    results = []

    for example in GOLDEN_DATASET:
        while True:
            try:
                start = time.perf_counter()

                pipeline_result = run_pipeline(
                    example.question,
                    llm_client,
                )

                elapsed = time.perf_counter() - start

                grade = grade_example(
                    example,
                    pipeline_result,
                )

                grade["latency_s"] = round(elapsed, 2)

                results.append(grade)

                print(
                    f"  [{grade['category']:15s}] "
                    f"{example.question[:50]:50s} -> {grade}"
                )

                # Success: move to the next example
                break

            except RateLimitError:
                print("\n Groq rate limit reached.")
                print("Waiting 60 seconds before retrying...\n")
                time.sleep(60)

    return summarize(results)


def summarize(results: list[dict]) -> dict:
    answerable = [
        r for r in results
        if "exact_match" in r
    ]

    unanswerable = [
        r for r in results
        if "correctly_flagged_unanswerable" in r
    ]

    summary = {
        "total_examples": len(results),
        "exact_match_rate": (
            round(
                sum(r["exact_match"] for r in answerable)
                / len(answerable),
                3,
            )
            if answerable
            else None
        ),
        "execution_match_rate": (
            round(
                sum(r["execution_match_score"] for r in answerable)
                / len(answerable),
                3,
            )
            if answerable
            else None
        ),
        "unanswerable_detection_rate": (
            round(
                sum(
                    r["correctly_flagged_unanswerable"]
                    for r in unanswerable
                )
                / len(unanswerable),
                3,
            )
            if unanswerable
            else None
        ),
        "avg_confidence": round(
            sum(r["confidence"] for r in results)
            / len(results),
            3,
        ),
    }

    return summary


if __name__ == "__main__":
    print("Running evaluation suite...\n")

    summary = run_eval_suite()

    print("\n" + "=" * 60)
    print("EVAL SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2))