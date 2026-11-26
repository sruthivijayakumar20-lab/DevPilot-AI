
from types import SimpleNamespace

from app.orchestrator.review_router import route_review, finish_review


def run_test(name, state, review_output, expected):
    ctx = SimpleNamespace(state=state)

    result = route_review(ctx, review_output)
    actual = result.actions.route

    status = "PASS" if actual == expected else "FAIL"

    print(
        f"{status}: {name} | "
        f"Expected: {expected} | Actual: {actual}"
    )

    if actual != expected:
        print("Router message:", result.output)

    return actual == expected


def main():
    results = []

    results.append(run_test(
        "Tests passed",
        {
            "testing_result": "TEST_STATUS: PASSED",
            "review_revision_count": 0,
        },
        "VERDICT: PASS",
        "passed",
    ))

    results.append(run_test(
        "No tests found",
        {
            "testing_result": "TEST_STATUS: NO_TESTS_FOUND",
            "review_revision_count": 0,
        },
        "VERDICT: PASS",
        "passed",
    ))

    results.append(run_test(
        "Implementation-related failure",
        {
            "testing_result": "TEST_STATUS: FAILED",
            "review_revision_count": 0,
        },
        "VERDICT: PASS\nTEST_ASSESSMENT: IMPLEMENTATION_RELATED",
        "revise",
    ))

    results.append(run_test(
        "Test execution error",
        {
            "testing_result": "TEST_STATUS: ERROR",
            "review_revision_count": 0,
        },
        "VERDICT: PASS",
        "manual_review",
    ))

    results.append(run_test(
        "Unrelated test failure",
        {
            "testing_result": "TEST_STATUS: FAILED",
            "review_revision_count": 0,
        },
        "VERDICT: PASS\nTEST_ASSESSMENT: UNRELATED",
        "manual_review",
    ))

    results.append(run_test(
        "Maximum correction attempts",
        {
            "testing_result": "TEST_STATUS: PASSED",
            "review_revision_count": 2,
        },
        "VERDICT: NEEDS_CHANGES",
        "max_attempts",
    ))

    ctx = SimpleNamespace(state={})
    finish_review(ctx, "VERDICT: PASS")

    saved = ctx.state.get("review_result") == "VERDICT: PASS"
    results.append(saved)

    print(f"{'PASS' if saved else 'FAIL'}: Final review result saved")

    print(f"\nResults: {sum(results)}/{len(results)} passed")

    if not all(results):
        raise SystemExit("Review router tests failed.")


if __name__ == "__main__":
    main()
