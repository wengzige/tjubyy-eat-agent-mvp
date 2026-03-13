"use client";

import { startTransition, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";

import { FeedbackPanel } from "@/components/FeedbackPanel";
import { parseAnswerToRecommendationResult } from "@/lib/answerFormatter";
import {
  fetchRecommendations,
  fetchTodayHotRanking,
  reportRankingClick,
  type HistoryMessage,
  type HotRankingItem,
} from "@/lib/api";
import { siteConfig } from "@/lib/siteConfig";

const QUICK_PROMPTS = siteConfig.quickPrompts;

const CAMPUS_HOT_RANKING_FALLBACK: HotRankingItem[] = siteConfig.hotRankingFallback;

const getTrendMeta = (trend: HotRankingItem["trend"], delta: number) => {
  if (trend === "up") {
    return { arrow: "↑", text: `较昨日 +${Math.abs(delta)}`, cls: "up" as const };
  }
  if (trend === "down") {
    return { arrow: "↓", text: `较昨日 -${Math.abs(delta)}`, cls: "down" as const };
  }
  return { arrow: "→", text: "较昨日 持平", cls: "flat" as const };
};

type QuerySignal = {
  label: string;
  value: string;
};

const signalRule = (query: string): QuerySignal[] => {
  const signals: QuerySignal[] = [];
  const text = query.trim();
  if (!text) return signals;

  const matchedLocation = siteConfig.locationAliases.find((item) => item.keywords.some((keyword) => text.includes(keyword)));
  if (matchedLocation) {
    signals.push({ label: "校区", value: matchedLocation.value });
  }

  const budgetMatch = text.match(/预算\s*([0-9]{1,3})/);
  if (budgetMatch?.[1]) signals.push({ label: "预算", value: `¥${budgetMatch[1]}以内` });

  if (/(夜宵|晚上|晚饭)/.test(text)) signals.push({ label: "场景", value: "夜间就餐" });
  else if (/(中午|午饭|赶时间)/.test(text)) signals.push({ label: "场景", value: "午间快餐" });
  else if (/(聚餐|室友|同学)/.test(text)) signals.push({ label: "场景", value: "多人聚餐" });
  else if (/(一个人|一人食)/.test(text)) signals.push({ label: "场景", value: "一人食" });

  if (/(不辣|清淡)/.test(text)) signals.push({ label: "口味", value: "清淡少辣" });
  else if (/(辣|重口)/.test(text)) signals.push({ label: "口味", value: "偏辣重口" });

  return signals.slice(0, 4);
};

const buildHighlight = (reason: string) => {
  const parts = reason
    .split(/[。.!！?？；;]/)
    .map((item) => item.trim())
    .filter(Boolean);
  return parts[0] || reason;
};

const displayOrFallback = (value: string, fallback = "未提供") => {
  const text = (value || "").trim();
  return text || fallback;
};

export default function HomePage() {
  const crestSrc = "/image/tju-provided-seal.png";
  const [query, setQuery] = useState(siteConfig.defaultQuery);
  const [history, setHistory] = useState<HistoryMessage[]>([]);
  const [answer, setAnswer] = useState("");
  const [chatId, setChatId] = useState<string | undefined>(undefined);
  const [uid] = useState("demo-user");
  const [crestAvailable, setCrestAvailable] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rankingOpen, setRankingOpen] = useState(false);
  const [rankingItems, setRankingItems] = useState<HotRankingItem[]>(CAMPUS_HOT_RANKING_FALLBACK);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [isComposerFocused, setIsComposerFocused] = useState(false);
  const [resultTransitionKey, setResultTransitionKey] = useState(0);
  const [currentBatchIndex, setCurrentBatchIndex] = useState(0);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const rankingWrapRef = useRef<HTMLDivElement>(null);
  const rankingLoadRef = useRef<(() => Promise<void>) | null>(null);

  const parsedRecommendation = useMemo(() => parseAnswerToRecommendationResult(answer), [answer]);
  const cards = parsedRecommendation.cards;
  const isStructured = parsedRecommendation.mode === "structured";
  const batchSize = isStructured ? Math.max(1, parsedRecommendation.batchSize) : 3;
  const batchCount = isStructured ? Math.max(1, Math.ceil(cards.length / batchSize)) : 1;
  const normalizedBatchIndex = batchCount > 0 ? currentBatchIndex % batchCount : 0;
  const visibleCards = useMemo(() => {
    if (!cards.length) return [];
    if (!isStructured) return cards.slice(0, 3);
    const start = normalizedBatchIndex * batchSize;
    return cards.slice(start, start + batchSize);
  }, [cards, isStructured, normalizedBatchIndex, batchSize]);
  const querySignals = useMemo(() => signalRule(query), [query]);
  const primaryCard = visibleCards[0];
  const secondaryCards = visibleCards.slice(1, 3);
  const primaryHighlight = useMemo(() => buildHighlight(primaryCard?.reason || ""), [primaryCard]);
  const showPrimaryReasonDetail = useMemo(() => {
    if (!primaryCard) return false;
    const compactReason = primaryCard.reason.replace(/[。.!！?？；;\s]+/g, "");
    const compactHighlight = primaryHighlight.replace(/[。.!！?？；;\s]+/g, "");
    return compactReason !== compactHighlight;
  }, [primaryCard, primaryHighlight]);
  const submitHint = useMemo(() => {
    if (typeof navigator === "undefined") {
      return "Enter 发送 · Shift+Enter 换行";
    }
    const isMac = /Mac|iPhone|iPad/i.test(navigator.platform);
    return isMac ? "Enter 发送 · Shift+Enter 换行 · Cmd+Enter 快速发送" : "Enter 发送 · Shift+Enter 换行 · Ctrl+Enter 快速发送";
  }, []);

  const submitQuery = async (nextQuery: string) => {
    const text = nextQuery.trim();
    if (!text || loading) return;

    try {
      setLoading(true);
      setError(null);

      const res = await fetchRecommendations({
        query: text,
        uid,
        chatId,
        history,
      });

      if (!res.ok) {
        setError(res.error || "暂时没有拿到推荐结果，请稍后再试。");
        return;
      }

      const nextAnswer = (res.answer || "").trim();
      setAnswer(nextAnswer);
      setCurrentBatchIndex(0);
      setHistory((prev) => [
        ...prev,
        { role: "user", content: text },
        { role: "assistant", content: nextAnswer },
      ]);

      const raw = (res.raw as { chat_id?: string } | undefined) || undefined;
      if (raw?.chat_id) {
        setChatId(raw.chat_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败，请检查网络后重试。");
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async () => {
    await submitQuery(query);
  };

  useEffect(() => {
    const onDown = (event: MouseEvent) => {
      const node = rankingWrapRef.current;
      if (!node || !rankingOpen) return;
      if (!node.contains(event.target as Node)) {
        setRankingOpen(false);
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setRankingOpen(false);
        setFeedbackOpen(false);
      }
    };

    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [rankingOpen]);

  useEffect(() => {
    if (!feedbackOpen) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = original;
    };
  }, [feedbackOpen]);

  useEffect(() => {
    if (!rankingOpen) return;
    let canceled = false;

    const loadRanking = async () => {
      try {
        setRankingLoading(true);
        const items = await fetchTodayHotRanking();
        if (!canceled && items.length > 0) {
          setRankingItems(items);
        }
      } catch {
        // Keep fallback ranking silently.
      } finally {
        if (!canceled) {
          setRankingLoading(false);
        }
      }
    };
    rankingLoadRef.current = loadRanking;

    void loadRanking();
    const timer = window.setInterval(() => {
      void loadRanking();
    }, 45_000);

    return () => {
      canceled = true;
      rankingLoadRef.current = null;
      window.clearInterval(timer);
    };
  }, [rankingOpen]);

  useEffect(() => {
    if (!answer) return;
    setResultTransitionKey((prev) => prev + 1);
  }, [answer, normalizedBatchIndex]);

  return (
    <main className="demo-page">
      <div className="atmo-layer atmo-wash" />
      <div className="leaf-layer leaf-primary" />
      <div className="leaf-layer leaf-secondary" />
      <div className="leaf-layer leaf-tertiary" />
      <div className="emblem-ambient" />

      <div className="demo-shell">
        <section className="hero-card">
          <div className="hero-grid">
            <div className="hero-copy">
              <div className="hero-top">
                <div className="hero-badge">{siteConfig.heroBadgeLabel}</div>
                <div className="emblem-widget" ref={rankingWrapRef}>
                  <button
                    type="button"
                    className="school-badge school-badge-btn"
                    aria-label={`${siteConfig.schoolName}校徽`}
                    aria-expanded={rankingOpen}
                    onClick={() => setRankingOpen((v) => !v)}
                  >
                    <span className="school-badge-icon">
                      {crestAvailable ? (
                        <img
                          src={crestSrc}
                          alt={`${siteConfig.schoolName}校徽`}
                          className="school-badge-logo"
                          onError={() => setCrestAvailable(false)}
                        />
                      ) : (
                        <span className="school-badge-fallback" aria-hidden>
                          天
                        </span>
                      )}
                    </span>
                    <span className="school-badge-text">
                      <b>{siteConfig.shortSchoolName}</b>
                      <em>{siteConfig.schoolName}</em>
                    </span>
                    <span className={`badge-caret ${rankingOpen ? "open" : ""}`} aria-hidden>
                      ▾
                    </span>
                  </button>

                  <section className={`ranking-popover ${rankingOpen ? "open" : ""}`} aria-hidden={!rankingOpen}>
                    <div className="ranking-head">
                      <div className="ranking-head-main">
                        <h3>校园热门榜</h3>
                        <p>基于近期查询与点击热度整理</p>
                      </div>
                      <button
                        type="button"
                        className="ranking-refresh-btn"
                        onClick={() => {
                          if (!rankingLoading) {
                            void rankingLoadRef.current?.();
                          }
                        }}
                        disabled={rankingLoading}
                        aria-label="刷新热门榜"
                      >
                        <span className={`refresh-icon ${rankingLoading ? "spinning" : ""}`} aria-hidden>
                          ↻
                        </span>
                        刷新
                      </button>
                    </div>
                    {rankingLoading && <div className="ranking-loading">正在更新今日榜单...</div>}
                    <div className="ranking-list">
                      {rankingItems.map((item, idx) => {
                        const trendMeta = getTrendMeta(item.trend, item.delta);
                        return (
                          <button
                            key={item.shop_id || item.name}
                            type="button"
                            className={`rank-item rank-${idx + 1}`}
                            style={{ "--rank-delay": `${idx * 45}ms` } as CSSProperties}
                            onClick={() => {
                              void reportRankingClick({
                                shopId: item.shop_id,
                                shopName: item.name,
                                uid,
                              });
                              setQuery(item.query);
                              setRankingOpen(false);
                            }}
                          >
                            <span className="rank-no">{idx + 1}</span>
                            <span className="rank-main">
                              <strong>
                                {item.name}
                                <span className={`rank-trend rank-trend-${trendMeta.cls}`}>{trendMeta.arrow}</span>
                              </strong>
                              <em>{item.tag}</em>
                              <small className={`rank-trend-text rank-trend-${trendMeta.cls}`}>{trendMeta.text}</small>
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </section>
                </div>
              </div>

              <h1>{siteConfig.agentName}</h1>
              <p>{siteConfig.heroDescription}</p>
              <div className="hero-stats">
                {siteConfig.heroHighlights.map((item) => (
                  <span className="hero-stat" key={item}>
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <aside className="hero-crest-panel" aria-label="天津大学校徽展示">
              <div className="hero-crest-ring">
                {crestAvailable ? (
                  <img
                    src={crestSrc}
                    alt={`${siteConfig.schoolName}校徽`}
                    className="hero-crest-image"
                    onError={() => setCrestAvailable(false)}
                  />
                ) : (
                  <div className="hero-crest-placeholder">请放入天津大学校徽 PNG</div>
                )}
              </div>
              <div className="hero-crest-caption">
                <span className="hero-crest-label">{siteConfig.heroSealLabel}</span>
                <strong>{siteConfig.heroSealTitle}</strong>
                <p>{siteConfig.heroSealDescription}</p>
              </div>
            </aside>
          </div>
        </section>

        <section className="composer-card">
          <div className="composer-title">今天想怎么吃？</div>
          <div className="signal-row" aria-live="polite">
            {querySignals.length > 0 ? (
              querySignals.map((item) => (
                <span className="signal-chip" key={`${item.label}-${item.value}`}>
                  <b>{item.label}</b>
                  <em>{item.value}</em>
                </span>
              ))
            ) : (
              <span className="signal-tip">{siteConfig.signalTip}</span>
            )}
          </div>
          <div className={`composer-input-wrap ${isComposerFocused ? "is-focused" : ""} ${loading ? "is-loading" : ""}`}>
            <textarea
              className="composer-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsComposerFocused(true)}
              onBlur={() => setIsComposerFocused(false)}
              placeholder={siteConfig.inputPlaceholder}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey || !e.shiftKey)) {
                  e.preventDefault();
                  void onSubmit();
                }
              }}
            />
            <button className="send-btn" onClick={() => void onSubmit()} disabled={loading || !query.trim()} aria-busy={loading}>
              {loading ? "生成中..." : "发送"}
            </button>
          </div>
          <div className="composer-foot">
            <span className="submit-hint">{submitHint}</span>
            <div className="composer-foot-actions">
              {loading && <span className="submit-feedback">正在理解你的偏好并匹配结果...</span>}
              <button
                type="button"
                className="feedback-entry-btn"
                onClick={() => setFeedbackOpen(true)}
              >
                <span aria-hidden>✦</span>
                信息补充 / 用餐反馈
              </button>
            </div>
          </div>
          <div className="chip-row">
            {QUICK_PROMPTS.map((item) => (
              <button
                key={item}
                className={`chip-btn ${query.trim() === item ? "is-active" : ""}`}
                onClick={() => {
                  setQuery(item);
                  void submitQuery(item);
                }}
                disabled={loading}
              >
                {item}
              </button>
            ))}
          </div>
        </section>

        {error && (
          <section className="state-card state-error">
            <h3>出错了</h3>
            <p>{error}</p>
          </section>
        )}

        <section className="content-grid">
          <div className="results-panel results-panel-full">
            <div className="section-head">
              <h2>推荐结果</h2>
              <div className="result-actions">
                <span>
                  {loading
                    ? "正在为你匹配最优选项..."
                    : parsedRecommendation.summary || "优先展示最匹配选项，其次给你备选"}
                </span>
                {isStructured && cards.length > batchSize && (
                  <button
                    type="button"
                    className="refresh-batch-btn"
                    onClick={() => {
                      startTransition(() => {
                        setCurrentBatchIndex((prev) => (prev + 1) % batchCount);
                      });
                    }}
                  >
                    换一批
                  </button>
                )}
              </div>
            </div>

            {loading && (
              <div className="result-stack">
                <article className="result-card result-card-primary skeleton">
                  <div className="skeleton-line lg" />
                  <div className="skeleton-line" />
                  <div className="skeleton-line" />
                  <div className="skeleton-tags">
                    <span />
                    <span />
                    <span />
                  </div>
                </article>
                <div className="secondary-grid">
                  {[0, 1].map((idx) => (
                    <article className="result-card result-card-secondary skeleton" key={idx}>
                      <div className="skeleton-line lg" />
                      <div className="skeleton-line" />
                      <div className="skeleton-line" />
                      <div className="skeleton-tags">
                        <span />
                        <span />
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}

            {!loading && !answer && !error && (
              <section className="state-card">
                <h3>{siteConfig.readyTitle}</h3>
                <p>{siteConfig.readyDescription}</p>
              </section>
            )}

            {!loading && answer && primaryCard && (
              <>
                <div className="result-stack" key={resultTransitionKey}>
                  <article className="result-card result-card-primary">
                    <div className="result-head">
                      <h3>{primaryCard.name}</h3>
                      <div className="result-head-right">
                        <span className="rank-tag champion">优先推荐</span>
                      </div>
                    </div>
                    <p className="primary-highlight">{displayOrFallback(primaryHighlight, "未提供推荐理由")}</p>
                    <div className="tag-list">
                      {primaryCard.tags.map((tag) => (
                        <span className="tag" key={`${primaryCard.name}-${tag}`}>
                          {tag}
                        </span>
                      ))}
                    </div>
                    <ul className="meta-list">
                      {showPrimaryReasonDetail && (
                        <li>
                          <strong>推荐理由</strong>
                          <p>{displayOrFallback(primaryCard.reason, "未提供推荐理由")}</p>
                        </li>
                      )}
                      <li>
                        <strong>推荐菜</strong>
                        <p>{displayOrFallback(primaryCard.dishes)}</p>
                      </li>
                      <li>
                        <strong>适合场景</strong>
                        <p>{displayOrFallback(primaryCard.scene)}</p>
                      </li>
                      <li>
                        <strong>可能不足</strong>
                        <p>{displayOrFallback(primaryCard.downside)}</p>
                      </li>
                    </ul>
                  </article>

                  <div className="secondary-grid">
                    {secondaryCards.map((card, idx) => (
                      <article className="result-card result-card-secondary" key={`${card.name}-${idx + 1}`} style={{ "--card-delay": `${140 + idx * 70}ms` } as CSSProperties}>
                        <div className="result-head">
                          <h3>{card.name}</h3>
                          <div className="result-head-right">
                            <span className="rank-tag">备选 {idx + 2}</span>
                          </div>
                        </div>
                        <p className="secondary-highlight">{displayOrFallback(buildHighlight(card.reason), "未提供推荐理由")}</p>
                        <div className="tag-list">
                          {card.tags.map((tag) => (
                            <span className="tag" key={`${card.name}-${tag}`}>
                              {tag}
                            </span>
                          ))}
                        </div>
                        <ul className="meta-list compact">
                          <li>
                            <strong>推荐菜</strong>
                            <p>{displayOrFallback(card.dishes)}</p>
                          </li>
                          <li>
                            <strong>适合场景</strong>
                            <p>{displayOrFallback(card.scene)}</p>
                          </li>
                          <li>
                            <strong>可能不足</strong>
                            <p>{displayOrFallback(card.downside)}</p>
                          </li>
                        </ul>
                      </article>
                    ))}
                  </div>
                </div>

              </>
            )}

            {!loading && answer && !primaryCard && (
              <section className="state-card">
                <h3>结果整理中</h3>
                <p>当前返回内容暂未整理为推荐卡片，建议换一种更具体的问法后再试。</p>
              </section>
            )}
          </div>
        </section>
      </div>

      <div
        className={`feedback-modal ${feedbackOpen ? "open" : ""}`}
        aria-hidden={!feedbackOpen}
        onClick={() => setFeedbackOpen(false)}
      >
        <div className="feedback-modal-scrim" />
        <section
          className="feedback-modal-panel"
          role="dialog"
          aria-modal="true"
          aria-label="校园美食反馈"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="feedback-modal-head">
            <div>
              <h3>校园美食共创</h3>
              <p>{siteConfig.feedbackIntro}</p>
            </div>
            <button
              type="button"
              className="feedback-modal-close"
              aria-label="关闭反馈面板"
              onClick={() => setFeedbackOpen(false)}
            >
              ×
            </button>
          </div>
          <div className="feedback-modal-body">
            <FeedbackPanel showHeader={false} />
          </div>
        </section>
      </div>
    </main>
  );
}
