# 天大吃什么 Agent MVP

面向天津大学北洋园校区的校园餐饮推荐 Agent（MVP）。

## 技术栈
- 前端: Next.js (TypeScript)
- 后端: FastAPI
- 模型: 腾讯混元 Lite（通过腾讯云 SecretId / SecretKey）
- 数据: CSV + SQLite

## 项目结构
- `docs/`: 需求文档、接口设计、页面草图
- `backend/`: FastAPI 服务、店铺数据、推荐逻辑、腾讯混元接入
- `frontend/`: Next.js 页面与组件

## 本地启动
1. 进入 `backend/` 安装依赖并运行 API。
2. 进入 `frontend/` 安装依赖并启动前端。
3. 默认开发地址：
   - 前端：`http://localhost:3000`
   - 后端：`http://localhost:8000`

## 部署建议
- 小白最省心：前后端一起部署到腾讯云轻量应用服务器，用 Nginx 反代同域名。
- 如果你后面想拆开部署：前端设置 `NEXT_PUBLIC_API_BASE_URL` 指向后端域名，并在后端配置 `CORS_ALLOW_ORIGINS`。
