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
