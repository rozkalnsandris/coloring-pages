-- SOURCE ONLY: unapplied additive cookie-session preparation for issue #182.
-- The existing likes, page_stats, triggers, daily_prints and v3 tables stay untouched.
-- A session row is pseudonymous: retention, expired-row cleanup and Like-count
-- archival must be approved before the new cookie routes can be enabled.
CREATE TABLE IF NOT EXISTS like_cookie_sessions (
  cookie_hash TEXT PRIMARY KEY
    CHECK (length(cookie_hash) = 64 AND cookie_hash NOT GLOB '*[^0-9a-f]*'),
  consent_notice_version INTEGER NOT NULL CHECK (consent_notice_version > 0),
  consent_recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at INTEGER NOT NULL CHECK (expires_at > 0)
);
CREATE INDEX IF NOT EXISTS idx_like_cookie_sessions_expiry
  ON like_cookie_sessions(expires_at);

-- 180-day expiry archive contains only page-level totals; not visitor/session IDs.
-- The existing likes triggers remain unchanged and continue to count active votes.
CREATE TABLE IF NOT EXISTS archived_like_totals (
  page_id TEXT PRIMARY KEY,
  like_count INTEGER NOT NULL DEFAULT 0 CHECK (like_count >= 0)
);
