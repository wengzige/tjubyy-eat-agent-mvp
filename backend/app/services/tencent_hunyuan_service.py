from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from app.models.schemas import ParsedSlots
from app.services.parser import parse_query
from app.services.recommender import recommend
from app.services.shop_repository import fetch_active_shops


JSON_SCHEMA_HINT = {
    "query": "用户原始问题",
    "summary": "一句话总结推荐思路",
    "batch_size": 3,
    "total_count": 3,
    "recommendations": [
        {
            "name": "店名",
            "score": 92,
            "reason": "为什么推荐",
            "recommend_dish": "推荐点什么，不确定时留空字符串",
            "scene_fit": "适合什么场景",
            "warning": "可能不足或提醒，不确定时给简短客观提醒",
        }
    ],
}


def validate_and_map_history(history: List[Dict[str, Any]]) -> Tuple[Optional[List[Dict[str, str]]], Optional[str]]:
    if not history:
        return [], None

    if history[0].get("role") != "user":
        return None, "history 第一条必须是 user。"

    mapped: List[Dict[str, str]] = []
    for idx, item in enumerate(history):
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role not in {"user", "assistant"}:
            return None, f"history[{idx}] role 仅允许 user/assistant。"
        if not content:
            return None, f"history[{idx}] content 不能为空。"
        mapped.append({"Role": role, "Content": content})

    return mapped[-6:], None


def _merge_query_with_history(query: str, history: List[Dict[str, Any]]) -> str:
    recent_user_messages = [
        str(item.get("content") or "").strip()
        for item in history
        if item.get("role") == "user" and str(item.get("content") or "").strip()
    ]
    merged = recent_user_messages[-3:] + [query.strip()]
    return "；".join(item for item in merged if item)


def _extract_json_candidate(answer: str) -> Optional[str]:
    text = answer.strip()
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if fenced and fenced.group(1):
        return fenced.group(1).strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace >= 0 and last_brace > first_brace:
        return text[first_brace:last_brace + 1].strip()

    return None


def _compose_scene_fit(candidate: Dict[str, Any]) -> str:
    parts = []
    scenes = str(candidate.get("scenes") or "").replace("|", "、")
    if scenes:
        parts.append(scenes)
    campus = str(candidate.get("campus") or "").strip()
    area = str(candidate.get("area") or "").strip()
    if campus and area:
        parts.append(f"{campus}·{area}")
    elif campus:
        parts.append(campus)
    return " / ".join(parts)


def _compose_recommend_dish(candidate: Dict[str, Any]) -> str:
    tags = [item.strip() for item in str(candidate.get("tags") or "").split("|") if item.strip()]
    tastes = [item.strip() for item in str(candidate.get("tastes") or "").split("|") if item.strip()]
    picks = tags[:2] + tastes[:1]
    return "、".join(dict.fromkeys(picks))


def _compose_warning(candidate: Dict[str, Any]) -> str:
    warnings: List[str] = []
    if int(candidate.get("avg_price") or 0) >= 30:
        warnings.append("人均会稍高一些")
    if "夜宵" in str(candidate.get("scenes") or ""):
        warnings.append("夜间高峰可能需要等位")
    else:
        warnings.append("饭点可能排队，建议错峰前往")
    return "；".join(warnings[:2])


def _compose_summary(query: str, parsed: ParsedSlots, total_count: int) -> str:
    signals = []
    if parsed.location:
        signals.append(parsed.location)
    if parsed.budget_max is not None:
        signals.append(f"预算 {parsed.budget_max} 元内")
    if parsed.taste:
        signals.append(parsed.taste)
    if parsed.scene:
        signals.append(parsed.scene)
    if parsed.time:
        signals.append(parsed.time)

    if signals:
        return f"结合{'、'.join(signals)}，先给你筛出 {total_count} 个更合适的选择。"
    return f"根据“{query}”的语义，先给你筛出 {total_count} 个相对更合适的选择。"


def _build_local_structured_answer(query: str, parsed: ParsedSlots, candidates: List[Dict[str, Any]]) -> str:
    payload = {
        "query": query,
        "summary": _compose_summary(query, parsed, len(candidates)),
        "batch_size": 3,
        "total_count": len(candidates),
        "recommendations": [
            {
                "name": item["name"],
                "score": int(item["score"]),
                "reason": item["reason"],
                "recommend_dish": _compose_recommend_dish(item),
                "scene_fit": _compose_scene_fit(item),
                "warning": _compose_warning(item),
            }
            for item in candidates
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _build_candidate_context(query: str, history: List[Dict[str, Any]]) -> Tuple[ParsedSlots, List[Dict[str, Any]]]:
    merged_query = _merge_query_with_history(query, history)
    parsed = parse_query(merged_query)
    raw_shop_map = {item["id"]: item for item in fetch_active_shops()}
    ranked = recommend(parsed, top_k=6)

    candidates: List[Dict[str, Any]] = []
    for item in ranked:
        shop = raw_shop_map.get(item.shop_id, {})
        candidates.append(
            {
                "shop_id": item.shop_id,
                "name": item.name,
                "campus": shop.get("campus", item.campus),
                "area": shop.get("area", ""),
                "avg_price": int(shop.get("avg_price", item.avg_price)),
                "open_hours": shop.get("open_hours", ""),
                "tastes": shop.get("tastes", ""),
                "scenes": shop.get("scenes", ""),
                "tags": "|".join(item.tags),
                "score": round(float(item.score) * 100),
                "reason": item.reason,
            }
        )

    return parsed, candidates


def _build_model_messages(
    query: str,
    history: List[Dict[str, str]],
    parsed: ParsedSlots,
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    system_prompt = (
        "你是天津大学北洋园校区的餐饮推荐助手。"
        "你只能依据我提供的候选店铺、字段和用户上下文进行推荐，不能虚构新店、价格、位置、营业时间。"
        "输出必须是一个严格的 JSON 对象，不要输出 Markdown，不要输出额外解释。"
        f"JSON 结构示意：{json.dumps(JSON_SCHEMA_HINT, ensure_ascii=False)}"
        "字段要求：score 为 0-100 的整数；recommend_dish、scene_fit、warning 可以简短，但不能胡编乱造。"
    )

    user_prompt = (
        f"用户当前问题：{query}\n"
        f"解析到的偏好：{json.dumps(parsed.model_dump(), ensure_ascii=False)}\n"
        f"候选店铺：{json.dumps(candidates, ensure_ascii=False)}\n"
        "请从候选店铺里给出最合适的推荐，recommendations 顺序即推荐顺序。"
        "summary 用一句中文概括推荐逻辑。"
    )

    messages: List[Dict[str, str]] = [{"Role": "system", "Content": system_prompt}]
    messages.extend(history)
    messages.append({"Role": "user", "Content": user_prompt})
    return messages


def ask_tencent_hunyuan(
    *,
    query: str,
    history: List[Dict[str, Any]],
    parsed: ParsedSlots,
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    secret_id = os.getenv("TENCENT_SECRET_ID", "").strip()
    secret_key = os.getenv("TENCENT_SECRET_KEY", "").strip()
    if not secret_id or not secret_key:
        return {
            "ok": False,
            "error": "TENCENT_SECRET_ID 或 TENCENT_SECRET_KEY 未配置。",
            "code": None,
            "raw": None,
        }

    mapped_history, history_error = validate_and_map_history(history)
    if history_error:
        return {
            "ok": False,
            "error": history_error,
            "code": None,
            "raw": {"history": history},
        }

    try:
        from tencentcloud.common import credential
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
    except ImportError:
        return {
            "ok": False,
            "error": "缺少腾讯云 SDK，请先安装 tencentcloud-sdk-python。",
            "code": None,
            "raw": None,
        }

    model = os.getenv("TENCENT_HUNYUAN_MODEL", "hunyuan-lite").strip() or "hunyuan-lite"
    region = os.getenv("TENCENT_HUNYUAN_REGION", "").strip()
    endpoint = os.getenv("TENCENT_HUNYUAN_ENDPOINT", "hunyuan.tencentcloudapi.com").strip() or "hunyuan.tencentcloudapi.com"
    timeout_seconds = int(float(os.getenv("TENCENT_HUNYUAN_TIMEOUT_SECONDS", "45")))
    temperature = float(os.getenv("TENCENT_HUNYUAN_TEMPERATURE", "0.2"))

    try:
        cred = credential.Credential(secret_id, secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = endpoint
        http_profile.reqTimeout = timeout_seconds
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        client = hunyuan_client.HunyuanClient(cred, region, client_profile)
        req = models.ChatCompletionsRequest()
        req.from_json_string(
            json.dumps(
                {
                    "Model": model,
                    "Messages": _build_model_messages(query, mapped_history or [], parsed, candidates),
                    "Stream": False,
                    "Temperature": temperature,
                },
                ensure_ascii=False,
            )
        )
        resp = client.ChatCompletions(req)
    except TencentCloudSDKException as exc:
        return {
            "ok": False,
            "error": f"请求腾讯混元失败: {exc}",
            "code": None,
            "raw": None,
        }

    try:
        body = json.loads(resp.to_json_string())
    except ValueError:
        return {
            "ok": False,
            "error": "腾讯混元返回了无法解析的响应。",
            "code": None,
            "raw": str(resp),
        }

    choices = body.get("Choices") or body.get("choices") or []
    if not choices:
        return {
            "ok": False,
            "error": "腾讯混元响应中缺少 Choices。",
            "code": None,
            "raw": body,
        }

    choice = choices[0]
    message = choice.get("Message") or choice.get("message") or {}
    answer = message.get("Content") or message.get("content")
    finish_reason = choice.get("FinishReason") or choice.get("finish_reason") or "stop"
    if not answer:
        return {
            "ok": False,
            "error": "腾讯混元响应成功，但未返回内容。",
            "code": None,
            "finishReason": finish_reason,
            "raw": body,
        }

    return {
        "ok": True,
        "answer": str(answer).strip(),
        "finishReason": finish_reason,
        "raw": body,
    }


def generate_recommendation_response(
    *,
    query: str,
    uid: Optional[str] = None,
    chat_id: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    history = history or []
    parsed, candidates = _build_candidate_context(query, history)
    fallback_answer = _build_local_structured_answer(query, parsed, candidates)

    model_result = ask_tencent_hunyuan(
        query=query,
        history=history,
        parsed=parsed,
        candidates=candidates,
    )
    if not model_result.get("ok"):
        return {
            "ok": True,
            "answer": fallback_answer,
            "finishReason": "fallback",
            "raw": {
                "provider": "local-rule-fallback",
                "fallback": True,
                "uid": uid,
                "chat_id": chat_id,
                "parsed": parsed.model_dump(),
                "candidates": candidates,
                "model_error": model_result.get("error"),
            },
        }

    normalized_answer = _extract_json_candidate(str(model_result.get("answer") or ""))
    if not normalized_answer:
        return {
            "ok": True,
            "answer": fallback_answer,
            "finishReason": "fallback",
            "raw": {
                "provider": "local-rule-fallback",
                "fallback": True,
                "uid": uid,
                "chat_id": chat_id,
                "parsed": parsed.model_dump(),
                "candidates": candidates,
                "model_error": "腾讯混元未返回可解析 JSON，已回退到本地结构化结果。",
                "provider_raw": model_result.get("raw"),
            },
        }

    return {
        "ok": True,
        "answer": normalized_answer,
        "finishReason": model_result.get("finishReason") or "stop",
        "raw": {
            "provider": "tencent-hunyuan",
            "fallback": False,
            "uid": uid,
            "chat_id": chat_id,
            "parsed": parsed.model_dump(),
            "candidates": candidates,
            "provider_raw": model_result.get("raw"),
        },
    }
