export type HistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type RecommendProxyRequest = {
  query: string;
  uid?: string;
  chatId?: string;
  history?: HistoryMessage[];
};

export type RecommendProxyResponse = {
  ok: boolean;
  answer?: string | null;
  raw?: unknown;
  error?: string | null;
  code?: number | null;
  finishReason?: string | null;
};

export type HotRankingItem = {
  rank: number;
  shop_id: string;
  name: string;
  tag: string;
  campus: string;
  avg_price: number;
  query: string;
};

export type HotRankingResponse = {
  updated_at: string;
  source: string;
  items: HotRankingItem[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchRecommendations(payload: RecommendProxyRequest): Promise<RecommendProxyResponse> {
  const res = await fetch(`${API_BASE_URL}/api/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }

  return res.json();
}

export async function fetchTodayHotRanking(): Promise<HotRankingItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/rankings/today`, {
    method: "GET",
  });

  if (!res.ok) {
    throw new Error(`Ranking request failed: ${res.status}`);
  }

  const data = (await res.json()) as HotRankingResponse;
  return data.items || [];
}
