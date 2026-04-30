import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.session import build_session_cookie_value


class SessionCookieSecurityPhase5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_session_phase5.db"
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

        with self.SessionLocal() as db:
            db.query(User).delete()
            db.commit()
            admin = User(email="phase5-admin@example.com", password_hash="x", role="admin")
            db.add(admin)
            db.commit()
            seed_rbac_defaults(db)
            self.admin_id = admin.id

    def test_valid_signed_session_works(self):
        cookie = {"mufasa_session": build_session_cookie_value(self.admin_id)}
        response = self.client.get("/admin/ai/overview", cookies=cookie)
        self.assertEqual(response.status_code, 200)

    def test_tampered_session_returns_401(self):
        signed = build_session_cookie_value(self.admin_id)
        payload, sig = signed.split(".", 1)
        tampered = {"mufasa_session": f"{payload}.tampered{sig}"}
        response = self.client.get("/admin/ai/overview", cookies=tampered)
        self.assertEqual(response.status_code, 401)

    def test_missing_session_returns_401(self):
        response = self.client.get("/admin/ai/overview")
        self.assertEqual(response.status_code, 401)

    def test_logout_clears_cookie(self):
        response = self.client.post("/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertIn("mufasa_session=", response.headers.get("set-cookie", ""))
        self.assertIn("Max-Age=0", response.headers.get("set-cookie", ""))

    def test_production_cookie_uses_secure_true(self):
        original_env = os.environ.get("ENVIRONMENT")
        try:
            os.environ["ENVIRONMENT"] = "production"
            join_response = self.client.post(
                "/auth/join",
                json={"email": "phase5-user@example.com", "password": "password123"},
            )
            self.assertEqual(join_response.status_code, 201)
            self.assertIn("Secure", join_response.headers.get("set-cookie", ""))
        finally:
            if original_env is None:
                os.environ.pop("ENVIRONMENT", None)
            else:
                os.environ["ENVIRONMENT"] = original_env


if __name__ == "__main__":
    unittest.main()
