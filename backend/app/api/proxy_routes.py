from fastapi import APIRouter, HTTPException

from app.core.campus_config import CAMPUS_PROFILE
from app.models.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    StoreNameSuggestionsResponse,
    WorkflowRecommendRequest,
    WorkflowRecommendResponse,
)
from app.services.feedback_repository import save_feedback, suggest_store_names
from app.services.tencent_hunyuan_service import generate_recommendation_response
from app.services.usage_events import log_query_event


proxy_router = APIRouter()


@proxy_router.post("/recommend", response_model=WorkflowRecommendResponse)
def recommend_via_model(req: WorkflowRecommendRequest) -> WorkflowRecommendResponse:
    log_query_event(req.query, uid=req.uid, source="tencent-hunyuan-hybrid")
    result = generate_recommendation_response(
        query=req.query,
        uid=req.uid,
        chat_id=req.chatId,
        history=[item.model_dump() for item in req.history],
    )
    return WorkflowRecommendResponse(**result)


@proxy_router.get("/stores/suggest", response_model=StoreNameSuggestionsResponse)
def store_name_suggestions_proxy(keyword: str = "") -> StoreNameSuggestionsResponse:
    if not keyword.strip():
        return StoreNameSuggestionsResponse(items=[])
    return StoreNameSuggestionsResponse(items=suggest_store_names(keyword=keyword.strip(), limit=8))


@proxy_router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback_proxy(req: FeedbackRequest) -> FeedbackResponse:
    if req.feedbackType == "dining_feedback":
        if req.rating is None:
            raise HTTPException(status_code=400, detail="吃后反馈需要评分（1-5）。")
        if not (req.comment or "").strip():
            raise HTTPException(status_code=400, detail="吃后反馈需要填写评论内容。")

    feedback_id = save_feedback(
        {
            "feedback_type": req.feedbackType,
            "store_name": req.storeName.strip(),
            "area": (req.area or "").strip() or None,
            "category": (req.category or "").strip() or None,
            "avg_price": req.avgPrice,
            "rating": req.rating,
            "scene_tags": ",".join(req.sceneTags) if req.sceneTags else None,
            "taste_tags": ",".join(req.tasteTags) if req.tasteTags else None,
            "feature_tags": ",".join(req.featureTags) if req.featureTags else None,
            "recommend_dish": (req.recommendDish or "").strip() or None,
            "short_intro": (req.shortIntro or "").strip() or None,
            "recommend_reason": (req.recommendReason or "").strip() or None,
            "comment": (req.comment or "").strip() or None,
            "warning_note": (req.warningNote or "").strip() or None,
            "source": (req.source or "frontend_user_feedback").strip() or "frontend_user_feedback",
        }
    )
    return FeedbackResponse(ok=True, id=feedback_id, message=CAMPUS_PROFILE.feedback_success_message)
