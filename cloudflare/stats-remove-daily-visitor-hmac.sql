-- SOURCE ONLY: post-Worker privacy cleanup for issue #182.
-- Apply only after the backend-first Worker that no longer reads/writes daily_visitors
-- is active and verified under a separate exact LIVE/D1 authorization.
-- Cloudflare D1 Time Travel may retain earlier recoverable states for its plan window.
DROP TABLE IF EXISTS daily_visitors;
