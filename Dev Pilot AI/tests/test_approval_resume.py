
import asyncio

from google.genai import types

from google.adk import Context, Workflow
from google.adk.apps import App, ResumabilityConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import START

from app.orchestrator.approval_gate import (
    ApprovalDecision,
    request_plan_approval,
    evaluate_approval,
    finish_rejected,
)


APP_NAME = "approval_test"


def create_test_plan() -> str:
    return "Test Plan: Create a simple Python calculator."


def finish_approved(ctx: Context, node_input: str) -> str:
    ctx.state["test_branch"] = "APPROVED"
    return "APPROVED_BRANCH_EXECUTED"


# Build a small workflow without any LLM agents.
test_workflow = Workflow(
    name="approval_test_workflow",
    edges=[
        (
            START,
            create_test_plan,
            request_plan_approval,
            evaluate_approval,
        ),
        (
            evaluate_approval,
            {
                "approved": finish_approved,
                "rejected": finish_rejected,
            },
        ),
    ],
)


app = App(
    name=APP_NAME,
    root_agent=test_workflow,
    resumability_config=ResumabilityConfig(
        is_resumable=True
    ),
)


async def run_approval_test(approved: bool):

    user_id = "approval_test_user"
    session_id = (
        "approval_approved"
        if approved
        else "approval_rejected"
    )

    session_service = InMemorySessionService()

    runner = Runner(
        app=app,
        session_service=session_service,
    )

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    print("\nStarting workflow:", session_id)

    # 1. Start the workflow.
    initial_message = types.Content(
        role="user",
        parts=[
            types.Part(text="Start approval test")
        ],
    )

    interrupt_event = None
    interrupt_call = None

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=initial_message,
    ):

        if event.content and event.content.parts:
            for part in event.content.parts:

                if (
                    part.function_call
                    and part.function_call.name == "adk_request_input"
                ):
                    interrupt_event = event
                    interrupt_call = part.function_call

    # 2. Verify that the workflow paused.
    if interrupt_call is None:
        raise RuntimeError(
            "Approval interrupt was not generated."
        )

    print("Approval interrupt received.")
    print("Interrupt ID:", interrupt_call.id)

    invocation_id = interrupt_event.invocation_id

    print("Invocation ID:", invocation_id)

    # 3. Prepare the user's approval/rejection response.
    response = {
        "approved": approved,
        "feedback": (
            "Approved in standalone test."
            if approved
            else "Rejected in standalone test."
        ),
    }

    resume_message = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=interrupt_call.id,
                    name="adk_request_input",
                    response=response,
                )
            )
        ],
    )

    # 4. Resume the interrupted workflow.
    print("Resuming workflow...")

    final_outputs = []

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        invocation_id=invocation_id,
        new_message=resume_message,
    ):

        if event.output is not None:
            print("Workflow output:", event.output)
            final_outputs.append(str(event.output))

    # 5. Verify the correct branch executed.
    expected = (
        "APPROVED_BRANCH_EXECUTED"
        if approved
        else "Implementation cancelled."
    )

    if not any(expected in output for output in final_outputs):
        raise RuntimeError(
            f"Expected branch output not found: {expected}"
        )

    print("PASS:", expected)


async def main():

    await run_approval_test(approved=True)
    await run_approval_test(approved=False)

    print("\nALL APPROVAL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
