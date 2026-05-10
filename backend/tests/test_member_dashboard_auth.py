import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie


class MemberDashboardAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path("/tmp/test_member_dashboard_auth.db")
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
            db.query(ActivityLog).delete()
            db.query(LeadershipAssessment).delete()
            db.query(MemberProfile).delete()
            db.query(UserRole).delete()
            db.query(RolePermission).delete()
            db.query(Role).delete()
            db.query(Permission).delete()
            db.query(User).delete()
            db.commit()

            member = User(email="dashboard-member@example.com", password_hash="x", role="member")
            subscriber = User(email="dashboard-subscriber@example.com", password_hash="x", role="subscriber")
            admin = User(email="dashboard-admin@example.com", password_hash="x", role="admin")
            superadmin = User(email="dashboard-superadmin@example.com", password_hash="x", role="superadmin")
            db.add_all([member, subscriber, admin, superadmin])
            db.commit()
            seed_rbac_defaults(db)

            self.member_id = member.id
            self.subscriber_id = subscriber.id
            self.admin_id = admin.id
            self.superadmin_id = superadmin.id
        finally:
            db.close()

    def _remove_role_permission(self, role_name: str, permission_name: str) -> None:
        from app.models import Permission, Role

        db = self.SessionLocal()
        try:
            role = db.query(Role).filter(Role.name == role_name).first()
            permission = db.query(Permission).filter(Permission.name == permission_name).first()
            self.assertIsNotNone(role)
            self.assertIsNotNone(permission)
            role.permissions.remove(permission)
            db.commit()
        finally:
            db.close()

    def test_member_overview_requires_session(self):
        response = self.client.get("/member/overview")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required")

    def test_member_overview_requires_permission(self):
        self._remove_role_permission("member", "member:read_overview_self")

        response = self.client.get("/member/overview", cookies=session_cookie(self.member_id))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Forbidden")

    def test_member_activity_requires_session(self):
        response = self.client.get("/member/activity")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required")

    def test_member_activity_requires_permission(self):
        self._remove_role_permission("member", "member:read_activity_self")

        response = self.client.get("/member/activity", cookies=session_cookie(self.member_id))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Forbidden")

    def test_member_role_has_dashboard_permissions(self):
        from app.authz import get_user_permissions
        from app.models import User

        db = self.SessionLocal()
        try:
            member = db.query(User).filter(User.id == self.member_id).first()
            permissions = get_user_permissions(db, member)
            self.assertIn("member:read_overview_self", permissions)
            self.assertIn("member:read_activity_self", permissions)
        finally:
            db.close()

    def test_subscriber_role_has_dashboard_permissions(self):
        from app.authz import get_user_permissions
        from app.models import User

        db = self.SessionLocal()
        try:
            subscriber = db.query(User).filter(User.id == self.subscriber_id).first()
            permissions = get_user_permissions(db, subscriber)
            self.assertIn("member:read_overview_self", permissions)
            self.assertIn("member:read_activity_self", permissions)
        finally:
            db.close()

    def test_admin_or_superadmin_dashboard_access_behavior(self):
        for user_id in (self.admin_id, self.superadmin_id):
            cookies = session_cookie(user_id)
            overview = self.client.get("/member/overview", cookies=cookies)
            activity = self.client.get("/member/activity", cookies=cookies)

            self.assertEqual(overview.status_code, 200)
            self.assertEqual(activity.status_code, 200)


class MemberDashboardFrontendStaticTests(unittest.TestCase):
    def test_member_dashboard_uses_shared_api_client_and_clear_auth_errors(self):
        src = Path("src/pages/MemberDashboard.jsx").read_text()
        self.assertIn('import { api } from "../api/api";', src)
        self.assertIn('api("/member/overview", { method: "GET" })', src)
        self.assertIn('api("/member/activity", { method: "GET" })', src)
        self.assertIn("err.status === 401", src)
        self.assertIn("err.status === 403", src)

    def test_dashboard_route_waits_for_auth_before_member_hydration(self):
        src = Path("src/App.jsx").read_text()
        self.assertIn("function DashboardRoute", src)
        self.assertIn("if (!authChecked)", src)
        self.assertIn('if (!user) return <Navigate to="/?auth=login" replace />;', src)
        self.assertIn("return isAdmin ? <AdminOperationsDashboard /> : <MemberDashboard />;", src)

    def test_shared_api_client_forces_include_credentials_for_member_calls(self):
        src = Path("src/api/api.js").read_text()
        self.assertIn('credentials: "include"', src)
        self.assertIn('"/member/overview"', src)
        self.assertIn('"/member/activity"', src)


if __name__ == "__main__":
    unittest.main()
