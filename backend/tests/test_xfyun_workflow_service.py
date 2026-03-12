from typing import Any, Dict

from app.services.xfyun_workflow_service import ask_workflow, validate_and_map_history


class DummyResponse:
    def __init__(self, status_code: int, body: Dict[str, Any]):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self) -> Dict[str, Any]:
        return self._body


class DummyClient:
    def __init__(self, response: DummyResponse):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, endpoint: str, headers: Dict[str, str], json: Dict[str, Any]) -> DummyResponse:
        return self.response


def test_history_validation_first_message_must_be_user() -> None:
    mapped, err = validate_and_map_history(
        [
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "hi"},
        ]
    )
    assert mapped is None
    assert err == "history 第一条必须是 user。"


def test_ask_workflow_returns_readable_error_when_key_missing(monkeypatch) -> None:
    monkeypatch.setenv("XFYUN_APP_ID", "7b367536")
    monkeypatch.delenv("XFYUN_API_KEY", raising=False)
    monkeypatch.delenv("XFYUN_API_SECRET", raising=False)
    result = ask_workflow(query="你好")
    assert result["ok"] is False
    assert "未配置" in result["error"]


def test_ask_workflow_returns_error_when_appid_missing(monkeypatch) -> None:
    monkeypatch.delenv("XFYUN_APP_ID", raising=False)
    monkeypatch.setenv("XFYUN_API_KEY", "k")
    monkeypatch.setenv("XFYUN_API_SECRET", "s")
    result = ask_workflow(query="你好")
    assert result["ok"] is False
    assert "XFYUN_APP_ID" in result["error"]


def test_ask_workflow_handles_business_error(monkeypatch) -> None:
    monkeypatch.setenv("XFYUN_APP_ID", "7b367536")
    monkeypatch.setenv("XFYUN_API_KEY", "k")
    monkeypatch.setenv("XFYUN_API_SECRET", "s")
    monkeypatch.setattr(
        "app.services.xfyun_workflow_service.httpx.Client",
        lambda timeout: DummyClient(
            DummyResponse(
                200,
                {
                    "code": 20369,
                    "message": "service busy",
                    "choices": [],
                },
            )
        ),
    )
    result = ask_workflow(query="你好")
    assert result["ok"] is False
    assert result["code"] == 20369
    assert "服务忙" in result["error"]


def test_ask_workflow_handles_success_response(monkeypatch) -> None:
    monkeypatch.setenv("XFYUN_APP_ID", "7b367536")
    monkeypatch.setenv("XFYUN_API_KEY", "k")
    monkeypatch.setenv("XFYUN_API_SECRET", "s")
    monkeypatch.setattr(
        "app.services.xfyun_workflow_service.httpx.Client",
        lambda timeout: DummyClient(
            DummyResponse(
                200,
                {
                    "code": 0,
                    "message": "ok",
                    "choices": [
                        {
                            "delta": {"content": "推荐答案"},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )
        ),
    )
    result = ask_workflow(query="你好")
    assert result["ok"] is True
    assert result["answer"] == "推荐答案"
    assert result["finishReason"] == "stop"
