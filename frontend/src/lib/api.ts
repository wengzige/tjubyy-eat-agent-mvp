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
