"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";

import { formatAnswerToCards } from "@/lib/answerFormatter";
import { fetchRecommendations, type HistoryMessage } from "@/lib/api";

const QUICK_PROMPTS = [
  "清水河附近，预算 25，一个人，想吃清淡一点",
  "沙河校区，晚上和室友聚餐，预算 35，想吃辣",
  "现在在清水河，夜宵有什么性价比高的推荐？",
  "中午赶时间，预算 20 内，离教学楼近一点",
];

const CAMPUS_HOT_RANKING = [
  { name: "李四面馆", tag: "夜宵热门", query: "清水河附近，夜宵想吃面，预算 30 内，有什么推荐？" },
  { name: "张三盖饭", tag: "一人食首选", query: "一个人吃，想要盖饭，预算 25 左右，推荐下清水河附近的店" },
  { name: "老成都冒菜", tag: "重口味必点", query: "想吃偏辣重口，预算 35，沙河校区附近有什么好吃的？" },
  { name: "东北饺子馆", tag: "不辣友好", query: "不太能吃辣，想吃饺子，预算 30 内，推荐下成电附近" },
  { name: "夜猫烧烤", tag: "聚餐人气王", query: "晚上和同学聚餐想吃烧烤，预算 40 左右，清水河有啥推荐？" },
];

type QuerySignal = {
  label: string;
  value: string;
};

const signalRule = (query: string): QuerySignal[] => {
  const signals: QuerySignal[] = [];
  const text = query.trim();
  if (!text) return signals;

  if (text.includes("清水河")) signals.push({ label: "校区", value: "清水河" });
  else if (text.includes("沙河")) signals.push({ label: "校区", value: "沙河" });

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

export default function HomePage() {
  const [query, setQuery] = useState("预算30，清水河，晚上和同学想吃辣的");
  const [history, setHistory] = useState<HistoryMessage[]>([]);
  const [answer, setAnswer] = useState("");
  const [chatId, setChatId] = useState<string | undefined>(undefined);
  const [uid] = useState("demo-user");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyExpanded, setHistoryExpanded] = useState(true);
  const [rankingOpen, setRankingOpen] = useState(false);
  const rankingWrapRef = useRef<HTMLDivElement>(null);

  const cards = useMemo(() => formatAnswerToCards(answer), [answer]);
  const conversation = useMemo(() => history.slice(-10), [history]);
  const querySignals = useMemo(() => signalRule(query), [query]);
  const primaryCard = cards[0];
  const secondaryCards = cards.slice(1, 3);

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

      const nextAnswer = res.answer || "";
      setAnswer(nextAnswer);
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

  const clearConversation = () => {
    setHistory([]);
    setAnswer("");
    setChatId(undefined);
    setError(null);
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
      }
    };

    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [rankingOpen]);

  return (
    <main className="demo-page">
      <div className="atmo-layer atmo-wash" />
      <div className="leaf-layer leaf-primary" />
      <div className="leaf-layer leaf-secondary" />
      <div className="leaf-layer leaf-tertiary" />
      <div className="emblem-ambient" />

      <div className="demo-shell">
        <section className="hero-card">
          <div className="hero-top">
            <div className="hero-badge">Campus AI Food Agent</div>
            <div className="emblem-widget" ref={rankingWrapRef}>
              <button
                type="button"
                className="school-badge school-badge-btn"
                aria-label="电子科技大学校徽"
                aria-expanded={rankingOpen}
                onClick={() => setRankingOpen((v) => !v)}
              >
                <span className="school-badge-icon">
                  <Image src="/image/xiaohui.png" alt="UESTC Emblem" width={36} height={36} priority />
                </span>
                <span className="school-badge-text">
                  <b>UESTC</b>
                  <em>电子科技大学</em>
                </span>
                <span className={`badge-caret ${rankingOpen ? "open" : ""}`} aria-hidden>
                  ▾
                </span>
              </button>

              <section className={`ranking-popover ${rankingOpen ? "open" : ""}`} aria-hidden={!rankingOpen}>
                <div className="ranking-head">
                  <h3>今日热门美食榜</h3>
                  <p>看看同学们今天都在吃什么</p>
                </div>
                <div className="ranking-list">
                  {CAMPUS_HOT_RANKING.map((item, idx) => (
                    <button
                      key={item.name}
                      type="button"
                      className={`rank-item rank-${idx + 1}`}
                      onClick={() => {
                        setQuery(item.query);
                        setRankingOpen(false);
                      }}
                    >
                      <span className="rank-no">{idx + 1}</span>
                      <span className="rank-main">
                        <strong>{item.name}</strong>
                        <em>{item.tag}</em>
                      </span>
                    </button>
                  ))}
                </div>
              </section>
            </div>
          </div>
          <h1>成电吃什么</h1>
          <p>你的校园吃饭决策助手，帮你在预算、口味、距离和场景之间快速做出更优选择。</p>
          <div className="hero-stats">
            <span>清水河 / 沙河</span>
            <span>多轮会话推荐</span>
            <span>结构化卡片展示</span>
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
              <span className="signal-tip">输入后自动识别条件：校区 / 预算 / 场景 / 口味</span>
            )}
          </div>
          <div className="composer-input-wrap">
            <textarea
              className="composer-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="例如：预算 30，清水河，2 个人，不太辣，想找晚饭"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void onSubmit();
                }
              }}
            />
            <button className="send-btn" onClick={() => void onSubmit()} disabled={loading || !query.trim()}>
              {loading ? "生成中..." : "发送"}
            </button>
          </div>
          <div className="chip-row">
            {QUICK_PROMPTS.map((item) => (
              <button
                key={item}
                className="chip-btn"
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
          <div className="results-panel">
            <div className="section-head">
              <h2>推荐结果</h2>
              <span>{loading ? "正在为你匹配最优选项..." : "优先展示最匹配选项，其次给你备选"}</span>
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
                <h3>准备就绪</h3>
                <p>输入你的需求，系统会给出适合校园场景的推荐，并自动整理成可展示卡片。</p>
              </section>
            )}

            {!loading && answer && primaryCard && (
              <>
                <div className="result-stack">
                  <article className="result-card result-card-primary">
                    <div className="result-head">
                      <h3>{primaryCard.name}</h3>
                      <span className="rank-tag champion">BEST MATCH</span>
                    </div>
                    <p className="primary-highlight">{buildHighlight(primaryCard.reason)}</p>
                    <div className="tag-list">
                      {primaryCard.tags.map((tag) => (
                        <span className="tag" key={`${primaryCard.name}-${tag}`}>
                          {tag}
                        </span>
                      ))}
                    </div>
                    <ul className="meta-list">
                      <li>
                        <strong>推荐理由</strong>
                        <p>{primaryCard.reason}</p>
                      </li>
                      <li>
                        <strong>推荐菜</strong>
                        <p>{primaryCard.dishes}</p>
                      </li>
                      <li>
                        <strong>适合场景</strong>
                        <p>{primaryCard.scene}</p>
                      </li>
                      <li>
                        <strong>可能不足</strong>
                        <p>{primaryCard.downside}</p>
                      </li>
                    </ul>
                  </article>

                  <div className="secondary-grid">
                    {secondaryCards.map((card, idx) => (
                      <article className="result-card result-card-secondary" key={`${card.name}-${idx + 1}`}>
                        <div className="result-head">
                          <h3>{card.name}</h3>
                          <span className="rank-tag">TOP {idx + 2}</span>
                        </div>
                        <p className="secondary-highlight">{buildHighlight(card.reason)}</p>
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
                            <p>{card.dishes}</p>
                          </li>
                          <li>
                            <strong>适合场景</strong>
                            <p>{card.scene}</p>
                          </li>
                          <li>
                            <strong>可能不足</strong>
                            <p>{card.downside}</p>
                          </li>
                        </ul>
                      </article>
                    ))}
                  </div>
                </div>

                <details className="raw-answer">
                  <summary>查看模型原始回答</summary>
                  <pre>{answer}</pre>
                </details>
              </>
            )}

            {!loading && answer && !primaryCard && (
              <section className="state-card">
                <h3>已返回结果</h3>
                <p>当前回答暂时无法结构化为店铺卡片，请展开原始回答查看完整内容。</p>
                <details className="raw-answer">
                  <summary>查看模型原始回答</summary>
                  <pre>{answer}</pre>
                </details>
              </section>
            )}
          </div>

          <aside className="chat-panel">
            <div className="chat-head">
              <h2>最近对话</h2>
              <div className="chat-actions">
                <button onClick={() => setHistoryExpanded((v) => !v)}>{historyExpanded ? "收起" : "展开"}</button>
                <button className="danger" onClick={clearConversation}>
                  清空
                </button>
              </div>
            </div>

            {conversation.length === 0 ? (
              <div className="empty-chat">还没有对话记录，先试试上面的示例问题。</div>
            ) : historyExpanded ? (
              <div className="chat-list">
                {conversation.map((item, idx) => (
                  <div className={`chat-bubble ${item.role}`} key={`${item.role}-${idx}`}>
                    <span className="chat-role">{item.role === "user" ? "你" : "Agent"}</span>
                    <p>{item.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-chat">对话已折叠，可点击“展开”查看。</div>
            )}
          </aside>
        </section>
      </div>
    </main>
  );
}
