type Shop = {
  shop_id: string;
  name: string;
  campus: string;
  avg_price: number;
  tags: string[];
  score: number;
  reason: string;
};

export default function RecommendationCard({ shop }: { shop: Shop }) {
  return (
    <article className="card">
      <div className="shop-title">
        <h3>{shop.name}</h3>
        <span className="muted">评分 {shop.score.toFixed(2)}</span>
      </div>
      <p className="muted">{shop.campus} | 人均 {shop.avg_price} 元</p>
      <div className="tags">
        {shop.tags.map((tag) => (
          <span key={`${shop.shop_id}-${tag}`} className="tag">
            {tag}
          </span>
        ))}
      </div>
      <p>{shop.reason}</p>
    </article>
  );
}
