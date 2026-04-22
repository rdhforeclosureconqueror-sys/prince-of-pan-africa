import os
import tempfile
import unittest
from pathlib import Path


class AuthSessionPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_auth_session.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        from app.database import Base, engine
        from app import models  # noqa: F401

        Base.metadata.create_all(bind=engine)

        from app.main import app
        from fastapi.testclient import TestClient

        cls.client = TestClient(app, base_url="https://testserver")

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.temp_dir.cleanup()

    def test_login_sets_cookie_with_cross_origin_flags_and_persists(self):
        join_res = self.client.post(
            "/auth/join",
            json={"email": "session-user@example.com", "password": "abcdef123"},
        )
        self.assertEqual(join_res.status_code, 200)

        login_res = self.client.post(
            "/auth/login",
            json={"email": "session-user@example.com", "password": "abcdef123"},
        )
        self.assertEqual(login_res.status_code, 200)

        set_cookie = login_res.headers.get("set-cookie", "")
        self.assertIn("mufasa_session=", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=none", set_cookie)
        self.assertIn("Secure", set_cookie)
        self.assertIn("Path=/", set_cookie)

        me_res = self.client.get("/auth/me")
        me_data = me_res.json()
        self.assertEqual(me_res.status_code, 200)
        self.assertTrue(me_data.get("authenticated"))
        self.assertEqual(me_data["user"]["email"], "session-user@example.com")

    def test_join_existing_email_returns_existing_user_without_duplication(self):
        first_join = self.client.post(
            "/auth/join",
            json={"email": "existing-user@example.com", "password": "abcdef123"},
        )
        self.assertEqual(first_join.status_code, 200)
        first_data = first_join.json()

        second_join = self.client.post(
            "/auth/join",
            json={"email": "existing-user@example.com", "password": "abcdef123"},
        )
        self.assertEqual(second_join.status_code, 200)
        second_data = second_join.json()

        self.assertTrue(second_data.get("existing"))
        self.assertFalse(second_data.get("joined"))
        self.assertEqual(first_data["user"]["id"], second_data["user"]["id"])


if __name__ == "__main__":
    unittest.main()
