# 讯飞星辰工作流接入说明

## 1. 环境变量配置
复制 `backend/.env.example` 到你自己的 `.env`，并填写：

- `XFYUN_APP_ID=7b367536`
- `XFYUN_FLOW_ID=7436739079683477504`
- `XFYUN_API_KEY=你的Key`
- `XFYUN_API_SECRET=你的Secret`
- `XFYUN_BASE_URL=https://xingchen-api.xf-yun.com`
- `XFYUN_TIMEOUT_SECONDS=20`

注意：`API_KEY` 和 `API_SECRET` 只允许存在于后端环境变量，不会暴露给前端。

## 2. 启动后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 3. 代理接口
- 路径：`POST /api/recommend`
- 作用：前端调用此接口，后端再调用讯飞工作流 `POST /workflow/v1/chat/completions`

请求体示例：
```json
{
  "query": "清水河附近，30元以内，一个人吃，不要太辣",
  "uid": "optional-user-id",
  "chatId": "optional-chat-id",
  "history": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好，有什么可以帮你？" }
  ]
}
```

成功返回示例：
```json
{
  "ok": true,
  "answer": "最终推荐文本",
  "finishReason": "stop",
  "raw": {}
}
```

失败返回示例：
```json
{
  "ok": false,
  "error": "错误描述",
  "code": 20369,
  "raw": {}
}
```

## 4. history 映射与校验
- 输入格式：`[{role, content}]`
- 转发格式：`[{role, content_type: "text", content}]`
- 校验规则：
  - 第一条必须是 `user`
  - role 只允许 `user/assistant`
  - content 不允许空

## 5. 本地测试
```bash
curl -X POST http://localhost:8000/api/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"清水河附近，30元以内，一个人吃，不要太辣\"}"
```
