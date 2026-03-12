export type RecommendProxyPayload = {
  query: string;
  uid?: string;
  chatId?: string;
  history?: Array<{ role: "user" | "assistant"; content: string }>;
};

export async function callRecommendProxy(payload: RecommendProxyPayload) {
  const res = await fetch("http://localhost:8000/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}
