from typing import Optional


class GenericModelAdapter:
    """
    通用模型接入预留。
    当前项目已在 tencent_hunyuan_service.py 中实现腾讯混元调用；
    如果后续要切换供应商，可以在这里继续抽象公共接口。
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or "tencent-hunyuan"

    def parse_or_rank(self, query: str) -> dict:
        return {
            "enabled": False,
            "provider": self.provider,
            "message": "Generic model adapter placeholder",
            "query": query,
        }
