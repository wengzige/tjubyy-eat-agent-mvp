# API Design (MVP)

## 1. 规则推荐
`POST /api/v1/recommend`

请求示例：
```json
{
  "query": "预算30，北洋园，晚上和同学吃辣点",
  "top_k": 3
}
```

## 2. 混元结构化推荐
`POST /api/recommend`

请求示例：
```json
{
  "query": "预算30，北洋园，晚上和同学吃辣点",
  "uid": "demo-user",
  "history": []
}
```

成功返回示例：
```json
{
  "ok": true,
  "answer": "{\"query\":\"预算30，北洋园，晚上和同学吃辣点\",\"summary\":\"结合预算、位置和口味，先给你筛出 3 个更合适的选择。\",\"batch_size\":3,\"total_count\":3,\"recommendations\":[{\"name\":\"北洋园麻辣香锅\",\"score\":93,\"reason\":\"人均 24 元，在预算内；位置匹配 北洋园；口味偏向 辣；适合 同学聚餐。\",\"recommend_dish\":\"麻辣香锅\",\"scene_fit\":\"同学聚餐 / 北洋园·学五生活区\",\"warning\":\"饭点可能排队，建议错峰前往\"}]}",
  "finishReason": "stop"
}
```
