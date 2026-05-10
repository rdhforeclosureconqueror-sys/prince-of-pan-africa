import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


REQUIRED_MEMBER_PERMISSIONS = {
    "member:read_overview_self",
    "member:read_activity_self",
}

REQUIRED_ORGANIZER_PERMISSIONS = {
    "book_organizer:create_self",
    "book_organizer:read_self",
    "book_organizer:update_self",
    "book_organizer:export_self",
}

REQUIRED_ADMIN_PERMISSIONS = REQUIRED_MEMBER_PERMISSIONS | REQUIRED_ORGANIZER_PERMISSIONS | {"admin:read_dashboard"}


class AuthCohesionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path("/tmp/test_auth_cohesion.db")
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
        from app.models import MemberProfile, Permission, Role, RolePermission, User, UserRole

        db = self.SessionLocal()
        try:
            db.query(MemberProfile).delete()
            db.query(UserRole).delete()
            db.query(RolePermission).delete()
            db.query(Role).delete()
            db.query(Permission).delete()
            db.query(User).delete()
            db.commit()

            users = [
                User(email="cohesion-admin@example.com", password_hash="x", role="admin"),
                User(email="cohesion-superadmin@example.com", password_hash="x", role="superadmin"),
                User(email="cohesion-subscriber@example.com", password_hash="x", role="subscriber"),
                User(email="cohesion-member@example.com", password_hash="x", role="member"),
            ]
            db.add_all(users)
            db.flush()
            for user in users:
                db.add(MemberProfile(user_id=user.id, role=user.role, attributes={"company": "Test"}))
            db.commit()
            seed_rbac_defaults(db)

            self.admin_id = users[0].id
            self.superadmin_id = users[1].id
            self.subscriber_id = users[2].id
            self.member_id = users[3].id
        finally:
            db.close()

    def _auth_me(self, user_id: int) -> dict:
        response = self.client.get("/auth/me", cookies=session_cookie(user_id))
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_auth_me_admin_returns_admin_role_and_permissions(self):
        data = self._auth_me(self.admin_id)

        self.assertEqual(data["user"]["role"], "admin")
        self.assertTrue(data["user"]["is_admin"])
        self.assertIn("admin", data["rbac"]["roles"])
        self.assertTrue(REQUIRED_ADMIN_PERMISSIONS.issubset(set(data["rbac"]["permissions"])))

    def test_auth_me_superadmin_returns_all_permissions(self):
        from app.authz import DEFAULT_PERMISSION_NAMES

        data = self._auth_me(self.superadmin_id)

        self.assertEqual(data["user"]["role"], "superadmin")
        self.assertTrue(data["user"]["is_admin"])
        self.assertIn("superadmin", data["rbac"]["roles"])
        self.assertEqual(set(DEFAULT_PERMISSION_NAMES), set(data["rbac"]["permissions"]))

    def test_auth_me_subscriber_returns_member_and_organizer_permissions(self):
        data = self._auth_me(self.subscriber_id)

        permissions = set(data["rbac"]["permissions"])
        self.assertFalse(data["user"]["is_admin"])
        self.assertIn("subscriber", data["rbac"]["roles"])
        self.assertTrue((REQUIRED_MEMBER_PERMISSIONS | REQUIRED_ORGANIZER_PERMISSIONS).issubset(permissions))
        self.assertNotIn("admin:read_dashboard", permissions)

    def test_auth_me_member_does_not_return_organizer_permissions(self):
        data = self._auth_me(self.member_id)

        permissions = set(data["rbac"]["permissions"])
        self.assertFalse(data["user"]["is_admin"])
        self.assertIn("member", data["rbac"]["roles"])
        self.assertTrue(REQUIRED_MEMBER_PERMISSIONS.issubset(permissions))
        self.assertTrue(REQUIRED_ORGANIZER_PERMISSIONS.isdisjoint(permissions))

    def test_admin_permission_required_for_operations_deck_api(self):
        member_response = self.client.get("/admin/ai/overview", cookies=session_cookie(self.member_id))
        admin_response = self.client.get("/admin/ai/overview", cookies=session_cookie(self.admin_id))

        self.assertEqual(member_response.status_code, 403)
        self.assertEqual(admin_response.status_code, 200)

    def test_auth_debug_me_returns_safe_current_user_trace(self):
        data = self.client.get("/auth/debug/me", cookies=session_cookie(self.admin_id)).json()

        self.assertEqual(data["email"], "cohesion-admin@example.com")
        self.assertEqual(data["users_role"], "admin")
        self.assertEqual(data["member_profile_role"], "admin")
        self.assertIn("admin", data["rbac_roles"])
        self.assertIn("admin:read_dashboard", data["rbac_permissions"])
        self.assertTrue(data["computed_is_admin"])
        self.assertTrue(data["computed_can_access_organizer"])
        self.assertNotIn("password_hash", data)
        self.assertNotIn("token", data)
        self.assertNotIn("cookie", data)


if __name__ == "__main__":
    unittest.main()
