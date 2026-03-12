from fastapi import APIRouter

from app.models.schemas import WorkflowRecommendRequest, WorkflowRecommendResponse
from app.services.usage_events import log_query_event
from app.services.xfyun_workflow_service import ask_workflow


proxy_router = APIRouter()


@proxy_router.post("/recommend", response_model=WorkflowRecommendResponse)
def recommend_via_workflow(req: WorkflowRecommendRequest) -> WorkflowRecommendResponse:
    log_query_event(req.query, uid=req.uid, source="workflow-recommend")
    result = ask_workflow(
        query=req.query,
        uid=req.uid,
        chat_id=req.chatId,
        history=[item.model_dump() for item in req.history],
    )
    return WorkflowRecommendResponse(**result)
