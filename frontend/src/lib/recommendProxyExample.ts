export type RecommendProxyPayload = {
  query: string;
  uid?: string;
  chatId?: string;
  history?: Array<{ role: "user" | "assistant"; content: string }>;
};

function resolveExampleBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  return "http://localhost:8000";
}

export async function callRecommendProxy(payload: RecommendProxyPayload) {
  const res = await fetch(`${resolveExampleBaseUrl()}/api/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}
