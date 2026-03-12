# 前端页面草图（MVP）

## 页面: `/`

[Header]
- 标题: 成电吃什么 Agent
- 副标题: 输入预算、位置、时间、口味和场景，快速拿到推荐

[Input Panel]
- 一个自然语言输入框（textarea）
- 示例提示（placeholder）
- 按钮: “生成推荐”

[Parsed Slots]
- 展示解析结果 chips:
  - 预算
  - 校区/位置
  - 场景
  - 口味
  - 时间

[Recommendation List]
- 3 张卡片（纵向）
- 每张卡片信息:
  - 店名
  - 人均
  - 校区
  - 标签
  - 推荐理由

[Footer]
- 说明: 当前为 MVP，数据为 mock 数据

## 交互流程
1. 用户输入自然语言并提交
2. 前端调用 `/api/v1/recommend`
3. 渲染 parsed 与 recommendations
4. 失败时展示错误提示
