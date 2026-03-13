# 腾讯云轻量应用服务器部署说明

适合小白的最短路径：前后端都放在一台腾讯云轻量应用服务器上，然后用 Nginx 反代成同一个域名。

## 推荐环境
- 系统：Ubuntu 22.04
- 端口：
  - 前端 Next.js：`3000`
  - 后端 FastAPI：`8000`
  - Nginx：`80/443`

## 1. 上传项目
把项目代码放到服务器，例如：

```bash
mkdir -p /srv/tju-eat-agent
cd /srv/tju-eat-agent
```

## 2. 启动后端
```bash
cd /srv/tju-eat-agent/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `backend/.env`：

```env
TENCENT_SECRET_ID=你的SecretId
TENCENT_SECRET_KEY=你的SecretKey
TENCENT_HUNYUAN_MODEL=hunyuan-lite
TENCENT_HUNYUAN_REGION=
TENCENT_HUNYUAN_ENDPOINT=hunyuan.tencentcloudapi.com
TENCENT_HUNYUAN_TIMEOUT_SECONDS=45
TENCENT_HUNYUAN_TEMPERATURE=0.2
CORS_ALLOW_ORIGINS=https://你的域名
SHOP_SEED_DATASET_ID=tju_beiyangyuan_v1
```

启动：

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 3. 启动前端
```bash
cd /srv/tju-eat-agent/frontend
npm install
npm run build
```

如果前后端同域名部署，可以不配 `.env.local`。

启动：

```bash
npm run start
```

## 4. Nginx 反代
示例配置：

```nginx
server {
    listen 80;
    server_name 你的域名;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

这样前端页面和 `/api/*` 都会走同一个域名，前端不需要额外跨域配置。

## 5. 你上线前至少要确认
- 轻量服务器防火墙放行 `80/443`
- 域名已经解析到这台服务器
- `backend/.env` 已填入腾讯云密钥
- 访问 `http://你的域名/api/v1/health` 返回 `{"status":"ok"}`
