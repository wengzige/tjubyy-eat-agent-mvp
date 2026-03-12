from typing import Any, List, Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    query: str = Field(..., min_length=1, description="自然语言查询")
    top_k: int = Field(default=3, ge=1, le=10)


class ParsedSlots(BaseModel):
    budget_max: Optional[int] = None
    location: Optional[str] = None
    scene: Optional[str] = None
    taste: Optional[str] = None
    time: Optional[str] = None


class ShopResult(BaseModel):
    shop_id: str
    name: str
    campus: str
    avg_price: int
    tags: List[str]
    score: float
    reason: str


class RecommendResponse(BaseModel):
    parsed: ParsedSlots
    recommendations: List[ShopResult]
    meta: dict


class HistoryMessage(BaseModel):
    role: str
    content: str


class WorkflowRecommendRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户输入")
    uid: Optional[str] = None
    chatId: Optional[str] = None
    history: List[HistoryMessage] = Field(default_factory=list)


class WorkflowRecommendResponse(BaseModel):
    ok: bool
    answer: Optional[str] = None
    raw: Optional[Any] = None
    error: Optional[str] = None
    code: Optional[int] = None
    finishReason: Optional[str] = None
