from fastapi import APIRouter, HTTPException

from app.models.schemas import RecommendRequest, RecommendResponse
from app.services.parser import parse_query
from app.services.recommender import recommend
from app.services.shop_repository import count_shops


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/filters")
def filters() -> dict:
    return {
        "locations": ["清水河", "沙河"],
        "scenes": ["一个人", "同学聚餐"],
        "tastes": ["辣", "清淡"],
        "times": ["早餐", "午餐", "晚餐", "夜宵"],
    }


@router.post("/recommend", response_model=RecommendResponse)
def recommend_api(req: RecommendRequest) -> RecommendResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query 不能为空")

    parsed = parse_query(req.query)
    items = recommend(parsed, req.top_k)

    return RecommendResponse(
        parsed=parsed,
        recommendations=items,
        meta={
            "total_candidates": count_shops(),
            "returned": len(items),
            "engine": "rule-based",
        },
    )
