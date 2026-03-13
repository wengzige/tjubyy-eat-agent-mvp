# Backend (FastAPI)

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 关键环境变量
- `TENCENT_SECRET_ID`: 腾讯云 SecretId
- `TENCENT_SECRET_KEY`: 腾讯云 SecretKey
- `TENCENT_HUNYUAN_MODEL`: 默认 `hunyuan-lite`
- `TENCENT_HUNYUAN_REGION`: 可为空
- `TENCENT_HUNYUAN_ENDPOINT`: 默认 `hunyuan.tencentcloudapi.com`
- `CORS_ALLOW_ORIGINS`: 允许的前端域名列表
- `SHOP_SEED_CSV_PATH`: 店铺种子数据路径
- `SQLITE_DB_PATH`: SQLite 文件路径

## SQLite Data Source
- 默认数据库：`data/chedian.db`
- 首次运行会按 `data/schema.sql` 建表，并从 `data/shops_tju_beiyangyuan.csv` 自动 seed。
- 如果 `SHOP_SEED_DATASET_ID` 变化，服务会重新导入店铺数据，方便你切换北洋园版本的数据集。

## 目录说明
- `app/main.py`: FastAPI 入口
- `app/api/routes.py`: 规则推荐 API
- `app/api/proxy_routes.py`: 腾讯混元结构化推荐 API
- `app/services/parser.py`: 规则解析
- `app/services/recommender.py`: 排序推荐
- `app/services/tencent_hunyuan_service.py`: 腾讯混元 SDK 调用与本地回退
- `app/services/shop_repository.py`: SQLite 仓储
- `app/core/campus_config.py`: 北洋园校园配置
- `data/shops_tju_beiyangyuan.csv`: 默认店铺 seed 数据
