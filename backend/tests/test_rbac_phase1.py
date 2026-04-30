import os
import tempfile
import unittest
from pathlib import Path


class RBACPhase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_rbac.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_seed_roles_and_permissions(self):
        from app.authz import DEFAULT_PERMISSION_NAMES, DEFAULT_ROLE_NAMES, seed_rbac_defaults
        from app.models import Permission, Role

        db = self.SessionLocal()
        try:
            seed_rbac_defaults(db)
            role_names = {row.name for row in db.query(Role).all()}
            permission_names = {row.name for row in db.query(Permission).all()}
            self.assertTrue(set(DEFAULT_ROLE_NAMES).issubset(role_names))
            self.assertTrue(set(DEFAULT_PERMISSION_NAMES).issubset(permission_names))
        finally:
            db.close()

    def test_legacy_role_backfill_and_default(self):
        from app.authz import get_user_role_names, seed_rbac_defaults
        from app.models import User, UserRole

        db = self.SessionLocal()
        try:
            admin_user = User(email="legacy-admin@example.com", password_hash="x", role="admin")
            unknown_user = User(email="legacy-unknown@example.com", password_hash="x", role="king")
            db.add_all([admin_user, unknown_user])
            db.commit()

            seed_rbac_defaults(db)
            db.refresh(admin_user)
            db.refresh(unknown_user)

            self.assertEqual(get_user_role_names(db, admin_user), ["admin"])
            self.assertEqual(get_user_role_names(db, unknown_user), ["member"])
            self.assertGreaterEqual(db.query(UserRole).filter(UserRole.user_id == admin_user.id).count(), 1)
            self.assertGreaterEqual(db.query(UserRole).filter(UserRole.user_id == unknown_user.id).count(), 1)
        finally:
            db.close()

    def test_permission_resolution_for_member_admin_superadmin(self):
        from app.authz import get_user_permissions, seed_rbac_defaults, user_has_permission
        from app.models import User

        db = self.SessionLocal()
        try:
            member = User(email="p1-member@example.com", password_hash="x", role="member")
            admin = User(email="p1-admin@example.com", password_hash="x", role="admin")
            superadmin = User(email="p1-superadmin@example.com", password_hash="x", role="superadmin")
            db.add_all([member, admin, superadmin])
            db.commit()

            seed_rbac_defaults(db)

            member_perms = get_user_permissions(db, member)
            admin_perms = get_user_permissions(db, admin)
            superadmin_perms = get_user_permissions(db, superadmin)

            self.assertIn("member:read_self", member_perms)
            self.assertNotIn("admin:manage_users", member_perms)

            self.assertIn("member:read_self", admin_perms)
            self.assertIn("admin:manage_users", admin_perms)
            self.assertIn("assessment:read_analytics", admin_perms)

            self.assertIn("system:run_dev_reset", superadmin_perms)
            self.assertIn("admin:manage_users", superadmin_perms)
            self.assertTrue(user_has_permission(db, superadmin, "voice:use_tts"))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
