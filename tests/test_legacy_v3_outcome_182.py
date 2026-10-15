"""Legacy v3 erasure response semantics and no false Like erasure claim."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKER=(ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")
NOTICE=(ROOT/"js/like-cookie-consent.js").read_text(encoding="utf-8")
DOC=(ROOT/"docs/LIKE_PRINT_COOKIE_REDESIGN_182.md").read_text(encoding="utf-8")


class LegacyOutcomeAndExpiryNoticeTests(unittest.TestCase):
    def test_v3_only_claims_likes_if_actual_rows_deleted(self):
        section=WORKER.split("async function eraseLegacyV3(env, request) {",1)[1].split("async function recordAggregatePrint",1)[0]
        self.assertIn("Number(results[0]?.meta?.changes)",section)
        self.assertIn("Number(results[1]?.meta?.changes)",section)
        self.assertIn("Number.isSafeInteger(likesDeleted)",section)
        self.assertIn("Number.isSafeInteger(credentialsRevoked)",section)
        self.assertIn("likes_deleted:likesDeleted",section)
        self.assertIn("credential_revoked:credentialsRevoked===1",section)
        self.assertIn("if (!likesDeleted && !credentialsRevoked)",section)
        self.assertNotIn('return json({ok:true,matched:true});',section)

    def test_user_notice_does_not_promise_post_expiry_self_service_erasure(self):
        self.assertIn("Solange der Cookie gültig ist",NOTICE)
        self.assertIn("nicht mehr möglich",NOTICE)
        self.assertIn("Nach der Anonymisierung",NOTICE)
        self.assertNotIn("Vor der Anonymisierung können Sie Ihre aktiven Likes löschen",NOTICE)
        self.assertIn("result?.likes_deleted === 0",NOTICE)
        self.assertIn("es wurden keine zugeordneten Likes gelöscht",NOTICE)
        self.assertIn("post-expiry erasure boundary",DOC)
        self.assertIn("browser cookie stops being sent",DOC)

    def test_post_expiry_cookie_cannot_be_used_as_secret_proof(self):
        # We explicitly do NOT introduce an extra identifier, TTL extension
        # or a privileged bypass around server-side cookie expiry validation.
        self.assertRegex(WORKER,r"expires_at>unixepoch\(\)")
        self.assertIn('if (!hash) return json({error:"like_cookie_required"},403);',WORKER)
        self.assertIn('LIKE_COOKIE_TTL_SECONDS = 180 * 24 * 60 * 60',WORKER)


if __name__=="__main__":
    unittest.main()
