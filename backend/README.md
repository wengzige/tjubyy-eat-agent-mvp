# Backend (FastAPI)

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## SQLite Data Source
- Default DB: `data/chedian.db`
- On first run, service auto-creates tables from `data/schema.sql` and seeds `shops` from `data/shops_mock.csv`.
- Optional override: set `SQLITE_DB_PATH` to custom sqlite file path.

## Scoring Config (YAML/JSON)
- Default file: `data/scoring_config.yaml`
- Optional override: set `SCORING_CONFIG_PATH` to a `.yaml/.yml/.json` file path.
- Config is loaded at request time, so you can tune weights without changing Python code.

## 目录说明
- `app/main.py`: FastAPI 入口
- `app/api/routes.py`: 路由层
- `app/services/parser.py`: 输入解析（规则）
- `app/services/recommender.py`: 排序与推荐（支持配置化权重）
- `app/services/shop_repository.py`: SQLite 数据仓储（建库/seed/查询）
- `app/services/model_adapter.py`: 讯飞模型接入预留
- `app/core/scoring_config.py`: 打分配置加载器
- `data/shops_mock.csv`: mock 店铺 seed 数据
- `data/schema.sql`: SQLite schema
- `data/scoring_config.yaml`: 默认打分配置
- `data/scoring_config.example.json`: JSON 配置示例
