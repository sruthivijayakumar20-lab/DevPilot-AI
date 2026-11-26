from google.adk import Workflow
from google.adk.workflow import START
from app.agents.repository_agent import repository_agent
from app.agents.planning_agent import planning_agent
from app.agents.coding_agent import coding_agent
from app.agents.review_agent import review_agent
from app.agents.final_report_agent import final_report_agent
from app.agents.testing_agent import testing_agent
from app.orchestrator.approval_gate import (
    request_plan_approval,
    evaluate_approval,
    finish_rejected,
)
from app.orchestrator.review_router import (
    route_review,
    finish_review,
)



development_workflow = Workflow(
    name="development_workflow",
    edges=[
        (
            START,
            repository_agent,
            planning_agent,
            request_plan_approval,
            evaluate_approval,
        ),
        (
            evaluate_approval,
            {
                "approved": coding_agent,
                "rejected": finish_rejected,
            },
        ),
        # Every implementation attempt must be tested and reviewed.
        (
            coding_agent,
            testing_agent,
            review_agent,
            route_review,
        ),
        (
            route_review,
            {
                "revise": coding_agent,
                "passed": finish_review,
                "manual_review": finish_review,
                "max_attempts": finish_review,
            },
        ),
        (
            finish_rejected,
            final_report_agent,
        ),
        (
            finish_review,
            final_report_agent,
        ),
    ],
)


