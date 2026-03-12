"use client";

import { useState } from "react";

type Props = {
  onSubmit: (query: string) => Promise<void>;
  loading: boolean;
};

export default function QueryForm({ onSubmit, loading }: Props) {
  const [query, setQuery] = useState("预算30，清水河，晚上和同学想吃辣的");

  return (
    <section className="card">
      <h3>输入你的需求</h3>
      <textarea
        className="input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="例如：预算 25，沙河，中午，一个人，想吃清淡点"
      />
      <button
        className="button"
        disabled={loading || !query.trim()}
        onClick={() => onSubmit(query)}
      >
        {loading ? "推荐中..." : "生成推荐"}
      </button>
    </section>
  );
}
