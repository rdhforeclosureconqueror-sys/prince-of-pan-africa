import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


class RBACPhase3MemberOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path("/tmp/test_rbac_phase3_member_ownership.db")
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
        from app.models import ActivityLog, LeadershipAssessment, Permission, Role, RolePermission, User, UserRole

        db = self.SessionLocal()
        try:
            db.query(UserRole).delete()
            db.query(RolePermission).delete()
            db.query(Role).delete()
            db.query(Permission).delete()
            db.query(ActivityLog).delete()
            db.query(LeadershipAssessment).delete()
            db.query(User).delete()
            db.commit()

            member_one = User(email="member-one-phase3@example.com", password_hash="x", role="member")
            member_two = User(email="member-two-phase3@example.com", password_hash="x", role="member")
            admin = User(email="admin-phase3@example.com", password_hash="x", role="admin")
            superadmin = User(email="superadmin-phase3@example.com", password_hash="x", role="superadmin")
            db.add_all([member_one, member_two, admin, superadmin])
            db.commit()

            seed_rbac_defaults(db)

            self.member_one_id = member_one.id
            self.member_two_id = member_two.id
            self.admin_id = admin.id
            self.superadmin_id = superadmin.id

            db.add_all(
                [
                    LeadershipAssessment(
                        user_id=self.member_one_id,
                        submission_id="sub-m1",
                        responses="{}",
                        scores="{}",
                        version="v1",
                    ),
                    LeadershipAssessment(
                        user_id=self.member_two_id,
                        submission_id="sub-m2",
                        responses="{}",
                        scores="{}",
                        version="v1",
                    ),
                    ActivityLog(user_id=self.member_one_id, action="member-one-action"),
                    ActivityLog(user_id=self.member_two_id, action="member-two-action"),
                ]
            )
            db.commit()
        finally:
            db.close()

    def test_unauthenticated_member_endpoints_return_401(self):
        overview_response = self.client.get("/member/overview")
        activity_response = self.client.get("/member/activity")

        self.assertEqual(overview_response.status_code, 401)
        self.assertEqual(activity_response.status_code, 401)

    def test_member_can_access_own_overview_and_activity(self):
        overview_response = self.client.get("/member/overview", cookies=session_cookie(self.member_one_id))
        activity_response = self.client.get("/member/activity", cookies=session_cookie(self.member_one_id))

        self.assertEqual(overview_response.status_code, 200)
        self.assertEqual(activity_response.status_code, 200)

        overview_payload = overview_response.json()
        activity_payload = activity_response.json()

        self.assertEqual(overview_payload["user"]["id"], self.member_one_id)
        self.assertEqual(overview_payload["summary_stats"]["assessment_count"], 1)
        self.assertEqual(overview_payload["summary_stats"]["activity_count"], 1)
        self.assertEqual(activity_payload["user_id"], self.member_one_id)
        self.assertEqual(len(activity_payload["activity"]), 1)
        self.assertEqual(activity_payload["activity"][0]["action"], "member-one-action")

    def test_second_member_cannot_receive_first_member_data(self):
        response = self.client.get("/member/activity", cookies=session_cookie(self.member_two_id))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["user_id"], self.member_two_id)
        self.assertEqual(len(payload["activity"]), 1)
        self.assertEqual(payload["activity"][0]["action"], "member-two-action")

    def test_query_param_user_id_override_attempt_is_ignored(self):
        response = self.client.get(
            f"/member/activity?user_id={self.member_one_id}",
            cookies=session_cookie(self.member_two_id),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["user_id"], self.member_two_id)
        self.assertEqual(len(payload["activity"]), 1)
        self.assertEqual(payload["activity"][0]["action"], "member-two-action")

    def test_admin_and_superadmin_can_only_access_their_own_member_scope(self):
        admin_response = self.client.get("/member/overview", cookies=session_cookie(self.admin_id))
        superadmin_response = self.client.get("/member/overview", cookies=session_cookie(self.superadmin_id))

        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(superadmin_response.status_code, 200)

        self.assertEqual(admin_response.json()["user"]["id"], self.admin_id)
        self.assertEqual(superadmin_response.json()["user"]["id"], self.superadmin_id)


if __name__ == "__main__":
    unittest.main()
