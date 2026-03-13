from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "tju-beiyangyuan-eat-agent-backend"
    app_env: str = "dev"
    engine: str = "tencent-hunyuan-hybrid"


settings = Settings()
