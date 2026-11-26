
import re

from google.adk import Context, Event


MAX_REVIEW_REVISIONS = 2


def route_review(ctx: Context, node_input: str):
    """
    Decide whether to finish, request corrections,
    or send the task for manual review.
    """

    # 1. Extract the Review Agent verdict.
    verdict_match = re.search(
        r"(?im)^\s*VERDICT\s*:\s*(PASS|NEEDS_CHANGES)\s*$",
        node_input
    )

    if not verdict_match:
        return Event(
            output=(
                "Manual review required. Invalid review verdict.\n\n"
                + node_input
            ),
            route="manual_review",
        )

    verdict = verdict_match.group(1).upper()

    # 2. Read the Testing Agent result.
    testing_result = ctx.state.get("testing_result", "")

    test_status_match = re.search(
        r"(?im)^\s*TEST_STATUS\s*:\s*"
        r"(PASSED|FAILED|NO_TESTS_FOUND|ERROR)\s*$",
        testing_result
    )

    if not test_status_match:
        return Event(
            output=(
                "Manual review required. Testing result is missing "
                "or invalid.\n\n"
                + str(testing_result)
            ),
            route="manual_review",
        )

    test_status = test_status_match.group(1).upper()

    # 3. Test execution errors require manual investigation.
    if test_status == "ERROR":
        return Event(
            output=(
                "Manual review required. Test execution encountered "
                "an error.\n\n"
                + str(testing_result)
                + "\n\nReview findings:\n"
                + node_input
            ),
            route="manual_review",
        )

    # 4. If tests failed, inspect the Review Agent's assessment.
    if test_status == "FAILED":

        assessment_match = re.search(
            r"(?im)^\s*TEST_ASSESSMENT\s*:\s*"
            r"(IMPLEMENTATION_RELATED|UNRELATED|INCONCLUSIVE)\s*$",
            node_input
        )

        if not assessment_match:
            return Event(
                output=(
                    "Manual review required. The Review Agent did not "
                    "provide a valid test failure assessment.\n\n"
                    + node_input
                ),
                route="manual_review",
            )

        assessment = assessment_match.group(1).upper()

        # Do not send the Coding Agent unnecessary corrections
        # for failures established as unrelated to implementation.
        if assessment == "UNRELATED":

            if verdict == "NEEDS_CHANGES":
                pass  # Continue to the correction logic below.

            else:
                return Event(
                    output=(
                        "Code review passed, but automated tests failed "
                        "for reasons assessed as unrelated to the "
                        "implementation. Manual verification is required.\n\n"
                        + node_input
                    ),
                    route="manual_review",
                )

        # If the cause cannot be determined, request manual review.
        elif assessment == "INCONCLUSIVE":
            return Event(
                output=(
                    "Manual review required. The cause of the test "
                    "failures could not be determined.\n\n"
                    + node_input
                ),
                route="manual_review",
            )

        # Implementation-related test failures require corrections.
        elif assessment == "IMPLEMENTATION_RELATED":
            verdict = "NEEDS_CHANGES"

    # 5. Finish if review passed.
    if verdict == "PASS":

        return Event(
            output=node_input,
            route="passed",
        )

    # 6. Count correction attempts.
    attempts = ctx.state.get("review_revision_count", 0) + 1

    ctx.state["review_revision_count"] = attempts

    if attempts > MAX_REVIEW_REVISIONS:
        return Event(
            output=(
                "Maximum correction attempts reached. "
                "Manual review is required.\n\n"
                + node_input
            ),
            route="max_attempts",
        )

    # 7. Send review feedback to the Coding Agent.
    original_plan = ctx.state.get("implementation_plan", "")

    return Event(
        output=(
            "ORIGINAL APPROVED IMPLEMENTATION PLAN:\n"
            f"{original_plan}\n\n"
            "REVIEW FEEDBACK — CORRECT THESE ISSUES:\n"
            f"{node_input}\n\n"
            "TESTING RESULTS:\n"
            f"{testing_result}\n\n"
            "Implement only the corrections within the "
            "original approved scope."
        ),
        route="revise",
    )


def finish_review(ctx: Context, node_input: str) -> str:
    """
    Save the final routing outcome for the Final Report Agent.
    """

    ctx.state["review_result"] = node_input

    return node_input
