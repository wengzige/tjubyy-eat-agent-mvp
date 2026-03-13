import type { HotRankingItem } from "@/lib/api";

export type LocationAlias = {
  value: string;
  keywords: string[];
};

export const siteConfig = {
  agentName: "天大吃什么",
  schoolName: "天津大学",
  shortSchoolName: "TJU",
  campusLabel: "北洋园 / 卫津路",
  heroDescription: "你的校园吃饭决策助手，帮你在预算、口味、距离和场景之间更快做出选择。",
  defaultQuery: "预算30，北洋园，晚上和同学想吃辣的",
  quickPrompts: [
    "北洋园附近，预算 25，一个人，想吃清淡一点",
    "北洋园校区，晚上和室友聚餐，预算 35，想吃辣",
    "现在在北洋园，夜宵有什么性价比高的推荐？",
    "中午赶时间，预算 20 内，离教学楼近一点",
  ],
  hotRankingFallback: [
    { rank: 1, shop_id: "kw-night", name: "#夜宵", tag: "等待更多搜索数据", campus: "", avg_price: 0, query: "北洋园附近，夜宵有什么推荐？", trend: "flat", delta: 0, today_count: 0, yesterday_count: 0 },
    { rank: 2, shop_id: "kw-single", name: "#一人食", tag: "等待更多搜索数据", campus: "", avg_price: 0, query: "一个人吃，预算 25 左右，有什么推荐？", trend: "flat", delta: 0, today_count: 0, yesterday_count: 0 },
    { rank: 3, shop_id: "kw-light", name: "#清淡", tag: "等待更多搜索数据", campus: "", avg_price: 0, query: "不辣清淡一点，有哪些推荐？", trend: "flat", delta: 0, today_count: 0, yesterday_count: 0 },
    { rank: 4, shop_id: "kw-group", name: "#聚餐", tag: "等待更多搜索数据", campus: "", avg_price: 0, query: "晚上和同学聚餐，预算 40 左右推荐什么？", trend: "flat", delta: 0, today_count: 0, yesterday_count: 0 },
    { rank: 5, shop_id: "kw-value", name: "#性价比", tag: "等待更多搜索数据", campus: "", avg_price: 0, query: "北洋园附近，性价比高的店有哪些？", trend: "flat", delta: 0, today_count: 0, yesterday_count: 0 },
  ] satisfies HotRankingItem[],
  locationAliases: [
    { value: "北洋园", keywords: ["北洋园", "北洋园校区", "天大北洋园"] },
    { value: "卫津路", keywords: ["卫津路", "卫津路校区", "七里台"] },
  ] satisfies LocationAlias[],
  inputPlaceholder: "例如：预算 30，北洋园，2 个人，不太辣，想找晚饭",
  signalTip: "输入后自动识别条件：校区 / 预算 / 场景 / 口味",
  readyTitle: "准备就绪",
  readyDescription: "输入你的需求，系统会结合北洋园校内外候选店铺给出推荐，并整理成可展示卡片。",
  feedbackIntro: "帮助更新北洋园美食地图，让推荐更懂天大学生口味。",
  feedbackAreaPlaceholder: "学一 / 学五 / 南门 / 校外",
  newStorePlaceholder: "例如：北洋园新开的砂锅店",
  diningStorePlaceholder: "例如：北洋园牛肉面",
};
