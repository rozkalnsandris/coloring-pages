-- Erasure write barrier. Separate approved migration before Worker activation.
CREATE TABLE IF NOT EXISTS like_erasure_blocks (
  visitor_hash TEXT PRIMARY KEY,
  blocked_until TEXT NOT NULL
);
