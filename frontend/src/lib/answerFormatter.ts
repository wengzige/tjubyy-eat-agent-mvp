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
  mode: "structured" | "legacy" | "empty";
  summary?: string;
  batchSize: number;
  totalCount: number;
  cards: RecommendationCardData[];
  parseError?: string;
};

const FIELD_PATTERNS = {
  name: /(店名|餐厅|店铺|推荐店名)[：:]\s*([^\n，。]+)/i,
  reason: /(推荐理由|理由)[：:]\s*([^\n]+)/i,
  dishes: /(推荐菜|招牌|必点|菜品)[：:]\s*([^\n]+)/i,
  scene: /(适合场景|场景|适合人群)[：:]\s*([^\n]+)/i,
  downside: /(可能不足|不足|注意事项|注意)[：:]\s*([^\n]+)/i,
};

function normalizeBlock(block: string): string {
  return block
    .replace(/\r/g, "")
    .replace(/[•*]/g, "-")
    .trim();
}

function hasCardSignals(block: string): boolean {
  const matches = block.match(/(店名|推荐理由|推荐菜|适合场景|可能不足)[：:]/g) || [];
  return matches.length >= 2;
}

function splitCandidateBlocks(text: string): string[] {
  const normalized = normalizeBlock(text);
  if (!normalized) return [];

  const byParagraph = normalized.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
  const structuredByParagraph = byParagraph.filter((block) => hasCardSignals(block));
  if (structuredByParagraph.length >= 1) return structuredByParagraph;
  if (byParagraph.length >= 2) return byParagraph;

  const byNumber = normalized
    .split(/\n(?=(?:\d+[.、]|[一二三四五六七八九十]+[、.]))/)
    .map((b) => b.trim())
    .filter(Boolean);
  const structuredByNumber = byNumber.filter((block) => hasCardSignals(block));
  if (structuredByNumber.length >= 1) return structuredByNumber;
  if (byNumber.length >= 2) return byNumber;

  return [normalized];
}

function extractFirstLineName(block: string, index: number): string {
  const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return `推荐 ${index + 1}`;

  const first = lines[0].replace(/^(?:\d+[.、]|[一二三四五六七八九十]+[、.])\s*/, "").trim();
  if (!first) return `推荐 ${index + 1}`;

  if (first.length <= 18) return first;
  return `推荐 ${index + 1}`;
}

function collectTags(card: RecommendationCardData): string[] {
  const tags: string[] = [];
  const source = `${card.scene} ${card.dishes} ${card.reason}`.toLowerCase();
  if (source.includes("一人") || source.includes("一个人")) tags.push("一人食");
  if (source.includes("夜宵")) tags.push("夜宵");
  if (source.includes("性价比") || source.includes("预算")) tags.push("性价比");
  if (source.includes("辣")) tags.push("辣味");
  if (source.includes("清淡")) tags.push("清淡");
  if (!tags.length) tags.push("校园推荐");
  return Array.from(new Set(tags)).slice(0, 4);
}

function parseBlock(block: string, index: number): RecommendationCardData {
  const safe = normalizeBlock(block);

  const nameMatch = safe.match(FIELD_PATTERNS.name);
  const reasonMatch = safe.match(FIELD_PATTERNS.reason);
  const dishesMatch = safe.match(FIELD_PATTERNS.dishes);
  const sceneMatch = safe.match(FIELD_PATTERNS.scene);
  const downsideMatch = safe.match(FIELD_PATTERNS.downside);

  const reasonFallback = safe.replace(/\n/g, " ").slice(0, 140).trim();

  const card: RecommendationCardData = {
    name: nameMatch?.[2]?.trim() || extractFirstLineName(safe, index),
    reason: reasonMatch?.[2]?.trim() || reasonFallback || "综合匹配度较高。",
    dishes: dishesMatch?.[2]?.trim() || "可根据当天口味选择店内招牌。",
    scene: sceneMatch?.[2]?.trim() || "适合日常校园就餐。",
    downside: downsideMatch?.[2]?.trim() || "高峰时段可能需要排队。",
    tags: [],
  };

  card.tags = collectTags(card);
  return card;
}

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
        reason: reason || "综合匹配度较高。",
        dishes: dishes || "可根据当天口味选择店内招牌。",
        scene: scene || "适合日常校园就餐。",
        downside: downside || "高峰时段可能需要排队。",
        tags: [],
        score,
      };
      card.tags = collectTags(card);
      return card;
    })
    .filter((item): item is RecommendationCardData => Boolean(item));
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

export function formatAnswerToCards(answer: string): RecommendationCardData[] {
  const blocks = splitCandidateBlocks(answer).slice(0, 4);
  return blocks.map((b, i) => parseBlock(b, i));
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
  if (jsonCandidate) {
    try {
      const parsed = JSON.parse(jsonCandidate) as StructuredRecommendationPayload;
      const cards = toStructuredCards(parsed);
      if (cards.length > 0) {
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
      }
    } catch {
      const legacyCards = formatAnswerToCards(text);
      return {
        mode: legacyCards.length ? "legacy" : "empty",
        batchSize: 3,
        totalCount: legacyCards.length,
        cards: legacyCards,
        parseError: "JSON parse failed",
      };
    }
  }

  const legacyCards = formatAnswerToCards(text);
  return {
    mode: legacyCards.length ? "legacy" : "empty",
    batchSize: 3,
    totalCount: legacyCards.length,
    cards: legacyCards,
  };
}
