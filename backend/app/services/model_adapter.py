from typing import Optional


class XunfeiModelAdapter:
    """
    讯飞模型接入预留。
    后续在此实现真实 API 调用，并返回结构化槽位或排序信号。
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret

    def parse_or_rank(self, query: str) -> dict:
        # TODO: 接入讯飞星火模型/大模型 API
        return {
            "enabled": False,
            "message": "Xunfei adapter placeholder",
            "query": query,
        }
