from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.proxy_routes import proxy_router
from app.api.routes import router

# Auto-load backend/.env for local development.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env', override=False)

app = FastAPI(title='成电吃什么 Agent API', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(router, prefix='/api/v1', tags=['mvp'])
app.include_router(proxy_router, prefix='/api', tags=['workflow-proxy'])
