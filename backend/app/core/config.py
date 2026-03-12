from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "chedian-eat-agent-backend"
    app_env: str = "dev"
    engine: str = "rule-based"


settings = Settings()
