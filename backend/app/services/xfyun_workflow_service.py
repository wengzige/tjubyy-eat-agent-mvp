import os
import time
from typing import Dict, List, Optional, Tuple

import httpx


ERROR_HINTS = {
    20204: "工作流未发布或仍是草稿，请先发布后重试。",
    20207: "工作流未发布或仍是草稿，请先发布后重试。",
    20369: "服务忙，请稍后再试。",
    20804: "OpenAPI 输出超时，请稍后再试。",
    23900: "对话超时或不存在，请检查 chatId 后重试。",
}


def _error_hint_by_code(code: Optional[int]) -> Optional[str]:
    if code is None:
        return None
    if code in ERROR_HINTS:
        return ERROR_HINTS[code]
    if 20900 <= code <= 20903:
        return "鉴权或额度异常，请检查 API Key/Secret、权限与额度。"
    return None


def _build_authorization() -> Tuple[Optional[str], Optional[str]]:
    api_key = os.getenv("XFYUN_API_KEY", "").strip()
    api_secret = os.getenv("XFYUN_API_SECRET", "").strip()
    if not api_key or not api_secret:
        return None, "XFYUN_API_KEY 或 XFYUN_API_SECRET 未配置。"
    return f"Bearer {api_key}:{api_secret}", None


def validate_and_map_history(history: List[Dict]) -> Tuple[Optional[List[Dict]], Optional[str]]:
    if not history:
        return [], None

    if history[0].get("role") != "user":
        return None, "history 第一条必须是 user。"

    mapped: List[Dict] = []
    for idx, item in enumerate(history):
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role not in {"user", "assistant"}:
            return None, f"history[{idx}] role 仅允许 user/assistant。"
        if not content:
            return None, f"history[{idx}] content 不能为空。"
        mapped.append(
            {
                "role": role,
                "content_type": "text",
                "content": content,
            }
        )

    return mapped, None


def _build_payload(
    query: str,
    uid: Optional[str],
    chat_id: Optional[str],
    mapped_history: List[Dict],
) -> Dict:
    payload: Dict = {
        "flow_id": os.getenv("XFYUN_FLOW_ID", "7436739079683477504"),
        "uid": uid or "demo-user",
        "parameters": {
            "AGENT_USER_INPUT": query,
        },
        "ext": {
            "bot_id": "workflow",
            "caller": "workflow",
        },
        "stream": False,
    }
    if chat_id:
        payload["chat_id"] = chat_id
    if mapped_history:
        payload["history"] = mapped_history
    return payload


def _is_retryable_request_error(exc: httpx.RequestError) -> bool:
    # 公网链路下 TLS EOF / 连接中断是典型瞬时错误，允许自动重试。
    if isinstance(exc, (httpx.ConnectError, httpx.ReadError, httpx.WriteError, httpx.RemoteProtocolError)):
        return True

    message = str(exc).lower()
    retryable_markers = (
        "unexpected_eof_while_reading",
        "eof occurred in violation of protocol",
        "connection reset",
        "connection aborted",
        "broken pipe",
        "temporarily unavailable",
        "tls",
        "ssl",
    )
    return any(marker in message for marker in retryable_markers)


def ask_workflow(
    query: str,
    uid: Optional[str] = None,
    chat_id: Optional[str] = None,
    history: Optional[List[Dict]] = None,
) -> Dict:
    app_id = os.getenv("XFYUN_APP_ID", "").strip()
    if not app_id:
        return {
            "ok": False,
            "error": "XFYUN_APP_ID 未配置。",
            "code": None,
            "raw": None,
        }

    auth_header, auth_err = _build_authorization()
    if auth_err:
        return {
            "ok": False,
            "error": auth_err,
            "code": None,
            "raw": None,
        }

    mapped_history, history_err = validate_and_map_history(history or [])
    if history_err:
        return {
            "ok": False,
            "error": history_err,
            "code": None,
            "raw": {"history": history},
        }

    base_url = os.getenv("XFYUN_BASE_URL", "https://xingchen-api.xf-yun.com").rstrip("/")
    endpoint = f"{base_url}/workflow/v1/chat/completions"
    timeout_seconds = float(os.getenv("XFYUN_TIMEOUT_SECONDS", "45"))
    max_retries = int(os.getenv("XFYUN_MAX_RETRIES", "2"))

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }
    payload = _build_payload(query=query, uid=uid, chat_id=chat_id, mapped_history=mapped_history or [])

    resp: Optional[httpx.Response] = None
    timeout_error: Optional[str] = None
    last_request_error: Optional[str] = None
    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=timeout_seconds, trust_env=False, http2=False) as client:
                resp = client.post(endpoint, headers=headers, json=payload)
            timeout_error = None
            last_request_error = None
            break
        except httpx.ReadTimeout:
            timeout_error = f"讯飞工作流响应超时（>{timeout_seconds}s），请稍后重试。"
            if attempt < max_retries:
                time.sleep(0.4 * (attempt + 1))
                continue
        except httpx.RequestError as exc:
            last_request_error = f"请求讯飞工作流失败: {exc}"
            if attempt < max_retries and _is_retryable_request_error(exc):
                time.sleep(0.4 * (attempt + 1))
                continue
            return {
                "ok": False,
                "error": last_request_error,
                "code": None,
                "raw": None,
            }

    if resp is None:
        return {
            "ok": False,
            "error": timeout_error or last_request_error or "请求讯飞工作流失败。",
            "code": 20804,
            "raw": None,
        }

    if resp.status_code != 200:
        return {
            "ok": False,
            "error": f"讯飞工作流 HTTP 错误: {resp.status_code}",
            "code": resp.status_code,
            "raw": resp.text,
        }

    try:
        body = resp.json()
    except ValueError:
        return {
            "ok": False,
            "error": "讯飞工作流返回了非 JSON 响应。",
            "code": None,
            "raw": resp.text,
        }

    code = body.get("code")
    if code != 0:
        message = body.get("message") or "讯飞工作流返回错误。"
        hint = _error_hint_by_code(code)
        error = f"{message}（code={code}）"
        if hint:
            error = f"{error} {hint}"
        return {
            "ok": False,
            "error": error,
            "code": code,
            "raw": body,
        }

    choice = (body.get("choices") or [{}])[0]
    delta = choice.get("delta") or {}
    answer = delta.get("content")
    finish_reason = choice.get("finish_reason")

    # 预留扩展: 后续可支持 interrupt/resume 相关分支。
    if finish_reason and finish_reason != "stop":
        return {
            "ok": False,
            "error": f"当前仅支持 finish_reason=stop，收到: {finish_reason}",
            "code": 0,
            "finishReason": finish_reason,
            "raw": body,
        }

    if not answer:
        return {
            "ok": False,
            "error": "响应成功但未获取到 choices[0].delta.content。",
            "code": 0,
            "finishReason": finish_reason,
            "raw": body,
        }

    return {
        "ok": True,
        "answer": answer,
        "finishReason": finish_reason,
        "raw": body,
    }
