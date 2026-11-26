from uuid import uuid4
from pydantic import BaseModel, Field
from google.adk import Context, Event
from google.adk.events import RequestInput


class ApprovalDecision(BaseModel):
    approved: bool = Field(
        description="Whether the user approves the implementation plan."
    )
    feedback: str | None = Field(
        default=None,
        description="Optional feedback from the user."
    )


def request_plan_approval(ctx: Context, node_input: str):
    """
    Display the implementation plan and pause for user approval.
    """

    # Save the implementation plan.
    ctx.state["implementation_plan"] = node_input

    # Mark the task as waiting for approval.
    ctx.state["task_status"] = "AWAITING_APPROVAL"

    # Clear results from any previous task.
    ctx.state["coding_result"] = ""
    ctx.state["testing_result"] = ""
    ctx.state["review_result"] = ""

    # Reset the correction counter for the new task.
    ctx.state["review_revision_count"] = 0

    return RequestInput(
        interrupt_id=f"implementation_plan_approval_{uuid4().hex}",
        message=(
            "Review the implementation plan:\n\n"
            f"{node_input}\n\n"
            "Please approve or reject this plan."
        ),
        payload={"plan": node_input},
        response_schema=ApprovalDecision,
    )


def evaluate_approval(
    ctx: Context,
    node_input: ApprovalDecision
):
    """Route the workflow based on the user's decision."""

    plan = ctx.state.get("implementation_plan", "")

    if node_input.approved:
        ctx.state["task_status"] = "APPROVED"

        return Event(
            output=plan,
            route="approved",
        )

    ctx.state["task_status"] = "CANCELLED"

    return Event(
        output=node_input.feedback or "Plan rejected by user.",
        route="rejected",
    )


def finish_rejected(ctx: Context, node_input: str) -> str:
    """
    Prepare workflow state when the user rejects the plan.
    """

    ctx.state["task_status"] = "CANCELLED"

    ctx.state["coding_result"] = "Coding was not started."
    ctx.state["testing_result"] = "Testing was not performed."
    ctx.state["review_result"] = "Code review was not performed."

    return (
        "Implementation cancelled.\n"
        f"Feedback: {node_input}"
    )
