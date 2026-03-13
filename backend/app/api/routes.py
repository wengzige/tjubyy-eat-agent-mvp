from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.campus_config import CAMPUS_PROFILE
from app.models.schemas import (
    EventAckResponse,
    FeedbackRequest,
    FeedbackResponse,
    HotRankingResponse,
    RankingClickEventRequest,
    RecommendRequest,
    RecommendResponse,
    StoreNameSuggestionsResponse,
)
from app.services.feedback_repository import save_feedback, suggest_store_names
from app.services.hot_ranking import get_today_hot_rankings
from app.services.parser import parse_query
from app.services.recommender import recommend
from app.services.shop_repository import count_shops
from app.services.usage_events import log_query_event, log_ranking_click_event


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/filters")
def filters() -> dict:
    return {
        "locations": list(CAMPUS_PROFILE.supported_locations),
        "scenes": list(CAMPUS_PROFILE.scene_labels),
        "tastes": list(CAMPUS_PROFILE.taste_labels),
        "times": list(CAMPUS_PROFILE.time_labels),
    }


@router.get("/rankings/today", response_model=HotRankingResponse)
def rankings_today() -> HotRankingResponse:
    items = get_today_hot_rankings(limit=5)
    return HotRankingResponse(
        updated_at=date.today().isoformat(),
        source="event-analytics",
        items=items,
    )


@router.post("/events/ranking-click", response_model=EventAckResponse)
def ranking_click_event(req: RankingClickEventRequest) -> EventAckResponse:
    log_ranking_click_event(
        shop_id=req.shop_id,
        shop_name=req.shop_name,
        uid=req.uid,
        source="web-ranking",
    )
    return EventAckResponse(ok=True)


@router.get("/stores/suggest", response_model=StoreNameSuggestionsResponse)
def store_name_suggestions(keyword: str = "") -> StoreNameSuggestionsResponse:
    if not keyword.strip():
        return StoreNameSuggestionsResponse(items=[])
    return StoreNameSuggestionsResponse(items=suggest_store_names(keyword=keyword.strip(), limit=8))


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(req: FeedbackRequest) -> FeedbackResponse:
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


@router.post("/recommend", response_model=RecommendResponse)
def recommend_api(req: RecommendRequest) -> RecommendResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    parsed = parse_query(req.query)
    items = recommend(parsed, req.top_k)
    log_query_event(req.query, source="rule-recommend")

    return RecommendResponse(
        parsed=parsed,
        recommendations=items,
        meta={
            "total_candidates": count_shops(),
            "returned": len(items),
            "engine": "rule-based",
        },
    )
