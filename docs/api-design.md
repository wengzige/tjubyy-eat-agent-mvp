# API Design (MVP)

## Base URL
`/api/v1`

## 1) 健康检查
- `GET /health`
- response:
```json
{ "status": "ok" }
```

## 2) 推荐接口
- `POST /recommend`

request:
```json
{
  "query": "预算30，清水河，晚上和同学吃辣点",
  "top_k": 3
}
```

response:
```json
{
  "parsed": {
    "budget_max": 30,
    "location": "清水河",
    "scene": "同学聚餐",
    "taste": "辣",
    "time": "晚餐"
  },
  "recommendations": [
    {
      "shop_id": "shop_001",
      "name": "川味小馆",
      "campus": "清水河",
      "avg_price": 26,
      "tags": ["川菜", "辣", "聚餐"],
      "score": 0.91,
      "reason": "预算内且口味匹配“辣”，距离清水河近，适合同学聚餐。"
    }
  ],
  "meta": {
    "total_candidates": 10,
    "returned": 3,
    "engine": "rule-based"
  }
}
```

## 3) 可用筛选项（可选）
- `GET /filters`
- 返回 location/scene/taste/time 候选值，供前端提示。

## 错误码约定
- `400`: 参数错误（query 为空）
- `500`: 服务内部错误

## 模型接入预留
- 当前 `engine = rule-based`
- 后续可切换 `engine = xunfei`，接口保持不变。
