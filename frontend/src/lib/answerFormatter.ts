export type RecommendationCardData = {
  name: string;
  reason: string;
  dishes: string;
  scene: string;
  downside: string;
  tags: string[];
  score?: number;
};

type StructuredRecommendationPayload = {
  query?: string;
  summary?: string;
  batch_size?: number;
  total_count?: number;
  recommendations?: Array<Record<string, unknown>>;
};

export type ParsedRecommendationResult = {
  mode: "structured" | "empty";
  summary?: string;
  batchSize: number;
  totalCount: number;
  cards: RecommendationCardData[];
  parseError?: string;
};

function normalizeScore(raw: unknown): number | undefined {
  if (typeof raw === "number" && Number.isFinite(raw)) {
    return Math.max(0, Math.min(100, Math.round(raw)));
  }

  if (typeof raw === "string") {
    const value = Number(raw.replace("%", "").trim());
    if (Number.isFinite(value)) {
      return Math.max(0, Math.min(100, Math.round(value)));
    }
  }

  return undefined;
}

function extractJsonCandidate(answer: string): string | null {
  const trimmed = answer.trim();
  if (!trimmed) return null;

  const fenceMatch = trimmed.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
  if (fenceMatch?.[1]) {
    return fenceMatch[1].trim();
  }

  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    return trimmed;
  }

  const firstBrace = trimmed.indexOf("{");
  const lastBrace = trimmed.lastIndexOf("}");
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    return trimmed.slice(firstBrace, lastBrace + 1);
  }

  return null;
}

function splitTagsFromCard(card: RecommendationCardData): string[] {
  const source = `${card.scene} ${card.dishes} ${card.reason}`.toLowerCase();
  const tags: string[] = [];
  if (source.includes("一个人") || source.includes("一人食")) tags.push("一人食");
  if (source.includes("夜宵")) tags.push("夜宵");
  if (source.includes("性价比") || source.includes("预算")) tags.push("性价比");
  if (source.includes("辣")) tags.push("辣味");
  if (source.includes("清淡")) tags.push("清淡");
  return Array.from(new Set(tags)).slice(0, 4);
}

function toStructuredCards(payload: StructuredRecommendationPayload): RecommendationCardData[] {
  const rawItems = Array.isArray(payload.recommendations) ? payload.recommendations : [];
  return rawItems
    .map((item, idx) => {
      const name = String(item.name || "").trim();
      const reason = String(item.reason || "").trim();
      const dishes = String(item.recommend_dish || "").trim();
      const scene = String(item.scene_fit || "").trim();
      const downside = String(item.warning || "").trim();
      const score = normalizeScore(item.score);

      if (!name && !reason && !dishes && !scene && !downside) {
        return null;
      }

      const card: RecommendationCardData = {
        name: name || `推荐 ${idx + 1}`,
        reason,
        dishes,
        scene,
        downside,
        tags: [],
        score,
      };
      card.tags = splitTagsFromCard(card);
      return card;
    })
    .filter((item): item is RecommendationCardData => Boolean(item));
}

export function parseAnswerToRecommendationResult(answer: string): ParsedRecommendationResult {
  const text = (answer || "").trim();
  if (!text) {
    return {
      mode: "empty",
      batchSize: 3,
      totalCount: 0,
      cards: [],
    };
  }

  const jsonCandidate = extractJsonCandidate(text);
  if (!jsonCandidate) {
    return {
      mode: "empty",
      batchSize: 3,
      totalCount: 0,
      cards: [],
      parseError: "No JSON candidate found",
    };
  }

  try {
    const parsed = JSON.parse(jsonCandidate) as StructuredRecommendationPayload;
    const cards = toStructuredCards(parsed);
    if (!cards.length) {
      return {
        mode: "empty",
        batchSize: 3,
        totalCount: 0,
        cards: [],
        parseError: "JSON parsed but recommendations is empty",
      };
    }

    const batchSizeRaw = Number(parsed.batch_size);
    const batchSize = Number.isFinite(batchSizeRaw) && batchSizeRaw > 0 ? Math.floor(batchSizeRaw) : 3;
    const totalCountRaw = Number(parsed.total_count);
    const totalCount = Number.isFinite(totalCountRaw) && totalCountRaw > 0 ? Math.floor(totalCountRaw) : cards.length;
    const summary = String(parsed.summary || "").trim();

    return {
      mode: "structured",
      summary: summary || undefined,
      batchSize,
      totalCount,
      cards,
    };
  } catch {
    return {
      mode: "empty",
      batchSize: 3,
      totalCount: 0,
      cards: [],
      parseError: "JSON parse failed",
    };
  }
}
