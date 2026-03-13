"use client";

import { useState } from "react";

import { siteConfig } from "@/lib/siteConfig";

type Props = {
  onSubmit: (query: string) => Promise<void>;
  loading: boolean;
};

export default function QueryForm({ onSubmit, loading }: Props) {
  const [query, setQuery] = useState(siteConfig.defaultQuery);

  return (
    <section className="card">
      <h3>输入你的需求</h3>
      <textarea
        className="input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={siteConfig.inputPlaceholder}
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
