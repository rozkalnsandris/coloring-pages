-- Apply this reviewed source migration separately before activating the v3 Worker.
-- A D1 schema source file is not a production migration.
CREATE TABLE IF NOT EXISTS visitor_credentials (
  visitor_hash TEXT PRIMARY KEY,
  like_allowed INTEGER NOT NULL CHECK (like_allowed IN (0, 1)),
  print_allowed INTEGER NOT NULL CHECK (print_allowed IN (0, 1)),
  notice_version INTEGER NOT NULL CHECK (notice_version > 0),
  consent_recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at INTEGER NOT NULL
);
