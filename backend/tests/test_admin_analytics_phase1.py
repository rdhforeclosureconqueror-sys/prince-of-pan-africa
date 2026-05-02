import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


class AdminAnalyticsPhase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path("/tmp/test_admin_analytics_phase1.db")
        if db_path.exists():
            db_path.unlink()

        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ENVIRONMENT"] = "test"
        os.environ["SESSION_SECRET"] = "test-session-secret"

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine
        from app.main import app

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal
        cls.client = TestClient(app)

    def setUp(self):
        from app.authz import seed_rbac_defaults
        from app.models import (
            ActivityLog,
            Audiobook,
            AudiobookChapterReflection,
            AudiobookProgress,
            LeadershipAssessment,
            MemberProfile,
            Permission,
            Role,
            RolePermission,
            User,
            UserRole,
        )

        db = self.SessionLocal()
        try:
            db.query(AudiobookChapterReflection).delete()
            db.query(AudiobookProgress).delete()
            db.query(Audiobook).delete()
            db.query(LeadershipAssessment).delete()
            db.query(ActivityLog).delete()
            db.query(MemberProfile).delete()
            db.query(UserRole).delete()
            db.query(RolePermission).delete()
            db.query(Role).delete()
            db.query(Permission).delete()
            db.query(User).delete()
            db.commit()

            admin = User(email="admin-analytics@example.com", password_hash="x", role="admin")
            member = User(email="member-analytics@example.com", password_hash="x", role="member")
            recent_member = User(
                email="recent-analytics@example.com",
                password_hash="x",
                role="member",
                created_at=datetime.utcnow() - timedelta(days=2),
            )
            db.add_all([admin, member, recent_member])
            db.commit()

            profile = MemberProfile(user_id=member.id, role="member")
            db.add(profile)

            assessment = LeadershipAssessment(
                user_id=member.id,
                submission_id="sub-analytics-1",
                responses="{}",
                scores="{}",
                created_at=datetime.utcnow() - timedelta(days=1),
            )
            db.add(assessment)

            audiobook = Audiobook(
                user_id=member.id,
                title="Analytics Book",
                author="Pilot",
                source_type="paste",
                source_text="abc",
                content_hash="hash-analytics-1",
            )
            db.add(audiobook)
            db.flush()

            progress = AudiobookProgress(audiobook_id=audiobook.id, user_id=member.id)
            reflection = AudiobookChapterReflection(
                audiobook_id=audiobook.id,
                user_id=member.id,
                chapter_index=0,
                prompt="thought",
                notes="note",
            )
            db.add_all([progress, reflection])

            older_activity = ActivityLog(
                user_id=member.id,
                action="older_action",
                timestamp=datetime.utcnow() - timedelta(days=10),
            )
            recent_activity = ActivityLog(
                user_id=recent_member.id,
                action="recent_action",
                timestamp=datetime.utcnow() - timedelta(hours=1),
            )
            db.add_all([older_activity, recent_activity])
            db.commit()

            seed_rbac_defaults(db)

            self.admin_id = admin.id
            self.member_id = member.id
        finally:
            db.close()

    def test_admin_overview_returns_real_counts(self):
        response = self.client.get("/admin/overview", cookies=session_cookie(self.admin_id))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["data"]["source"], "placeholder_removed")
        metrics = payload["data"]["metrics"]

        self.assertEqual(metrics["total_users"]["value"], 3)
        self.assertEqual(metrics["total_member_profiles"]["value"], 1)
        self.assertEqual(metrics["total_activity_logs"]["value"], 2)
        self.assertEqual(metrics["total_leadership_assessments"]["value"], 1)
        self.assertEqual(metrics["total_audiobooks"]["value"], 1)
        self.assertEqual(metrics["total_audiobook_progress_records"]["value"], 1)
        self.assertEqual(metrics["total_reflections"]["value"], 1)
        self.assertEqual(metrics["new_users_last_7_days"]["value"], 3)
        self.assertEqual(metrics["active_users_last_7_days"]["value"], 1)
        self.assertEqual(metrics["users_by_role"]["value"].get("admin"), 1)
        self.assertEqual(metrics["users_by_role"]["value"].get("member"), 2)
        self.assertTrue(all(metric["source"] == "real" for metric in metrics.values()))

    def test_activity_stream_returns_seeded_activity_logs(self):
        response = self.client.get("/admin/activity-stream", cookies=session_cookie(self.admin_id))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["source"], "placeholder_removed")
        self.assertGreaterEqual(len(payload["items"]), 2)
        self.assertEqual(payload["items"][0]["action"], "recent_action")
        self.assertEqual(payload["items"][1]["action"], "older_action")
        self.assertTrue(all(item["data_source"] == "real" for item in payload["items"]))

    def test_member_cannot_access_admin_analytics(self):
        response = self.client.get("/admin/overview", cookies=session_cookie(self.member_id))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get("/admin/overview")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
