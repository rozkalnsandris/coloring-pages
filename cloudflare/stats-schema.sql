PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS page_stats (
  page_id TEXT PRIMARY KEY,
  print_count INTEGER NOT NULL DEFAULT 0 CHECK (print_count >= 0),
  like_count INTEGER NOT NULL DEFAULT 0 CHECK (like_count >= 0),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS daily_prints (
  page_id TEXT NOT NULL,
  day TEXT NOT NULL,
  print_count INTEGER NOT NULL DEFAULT 0 CHECK (print_count >= 0),
  PRIMARY KEY (page_id, day)
);
CREATE TABLE IF NOT EXISTS likes (
  page_id TEXT NOT NULL,
  visitor_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (page_id, visitor_hash)
);
CREATE INDEX IF NOT EXISTS idx_daily_prints_day ON daily_prints(day, print_count DESC);
CREATE TRIGGER IF NOT EXISTS likes_after_insert
AFTER INSERT ON likes
BEGIN
  INSERT INTO page_stats (page_id, like_count, updated_at)
  VALUES (NEW.page_id, 1, datetime('now'))
  ON CONFLICT(page_id) DO UPDATE SET like_count=like_count+1, updated_at=datetime('now');
END;
CREATE TRIGGER IF NOT EXISTS likes_after_delete
AFTER DELETE ON likes
BEGIN
  UPDATE page_stats
  SET like_count=MAX(like_count-1,0), updated_at=datetime('now')
  WHERE page_id=OLD.page_id;
END;

CREATE TABLE IF NOT EXISTS daily_views (
  page_id TEXT NOT NULL,
  day TEXT NOT NULL,
  view_count INTEGER NOT NULL DEFAULT 0 CHECK (view_count >= 0),
  PRIMARY KEY (page_id, day)
);
CREATE INDEX IF NOT EXISTS idx_daily_views_day ON daily_views(day, view_count DESC);

CREATE TABLE IF NOT EXISTS daily_visitors (
  day TEXT NOT NULL,
  visitor_hash TEXT NOT NULL,
  PRIMARY KEY (day, visitor_hash)
);
