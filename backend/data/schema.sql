CREATE TABLE IF NOT EXISTS shops (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  campus TEXT NOT NULL,
  area TEXT,
  avg_price INTEGER NOT NULL,
  open_hours TEXT,
  tastes TEXT,
  scenes TEXT,
  tags TEXT,
  is_open INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  raw_query TEXT NOT NULL,
  parsed_json TEXT NOT NULL,
  result_json TEXT NOT NULL,
  engine TEXT NOT NULL DEFAULT 'rule-based',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL, -- query | ranking_click
  uid TEXT,
  query_text TEXT,
  shop_id TEXT,
  shop_name TEXT,
  source TEXT DEFAULT 'web',
  meta_json TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_events_type_time
  ON usage_events(event_type, created_at);

CREATE INDEX IF NOT EXISTS idx_usage_events_shop_time
  ON usage_events(shop_id, created_at);
