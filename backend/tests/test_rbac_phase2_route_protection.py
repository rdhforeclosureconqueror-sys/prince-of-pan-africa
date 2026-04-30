import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


class RBACPhase2RouteProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_rbac_phase2.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ENVIRONMENT"] = "test"
        os.environ["SESSION_SECRET"] = "test-session-secret"

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine
        from app.main import app

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        from app.authz import seed_rbac_defaults
        from app.models import User

        db = self.SessionLocal()
        try:
            db.query(User).delete()
            db.commit()

            member = User(email="member-phase2@example.com", password_hash="x", role="member")
            admin = User(email="admin-phase2@example.com", password_hash="x", role="admin")
            superadmin = User(email="superadmin-phase2@example.com", password_hash="x", role="superadmin")
            db.add_all([member, admin, superadmin])
            db.commit()

            seed_rbac_defaults(db)

            self.member_id = member.id
            self.admin_id = admin.id
            self.superadmin_id = superadmin.id
        finally:
            db.close()

    def test_unauthenticated_admin_request_rejected(self):
        response = self.client.get("/admin/ai/overview")
        self.assertEqual(response.status_code, 401)

    def test_member_cannot_access_admin_route(self):
        response = self.client.get("/admin/ai/overview", cookies=session_cookie(self.member_id))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_admin_route(self):
        response = self.client.get("/admin/ai/overview", cookies=session_cookie(self.admin_id))
        self.assertEqual(response.status_code, 200)

    def test_superadmin_can_access_all_protected_admin_and_system_routes(self):
        protected_routes = [
            ("get", "/admin/ai/overview"),
            ("get", "/admin/members"),
            ("get", "/admin/activity-stream"),
            ("get", "/system/verification"),
            ("get", "/system/verification/full"),
            ("post", "/system/database/reset-local?dev_confirm=false"),
        ]
        cookies = session_cookie(self.superadmin_id)
        for method, route in protected_routes:
            response = getattr(self.client, method)(route, cookies=cookies)
            self.assertEqual(response.status_code, 200, f"{method.upper()} {route} returned {response.status_code}")

    def test_dev_reset_blocked_outside_dev_or_test_environment(self):
        os.environ["ENVIRONMENT"] = "production"
        try:
            response = self.client.post(
                "/system/database/reset-local?dev_confirm=true",
                cookies=session_cookie(self.superadmin_id),
            )
            self.assertEqual(response.status_code, 403)
        finally:
            os.environ["ENVIRONMENT"] = "test"


if __name__ == "__main__":
    unittest.main()
