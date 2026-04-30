import os
import tempfile
import unittest
from pathlib import Path


class AuthPasswordMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_auth.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        from app.database import Base, SessionLocal, engine
        from app import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_new_user_hash_uses_pbkdf2(self):
        from app.models import User
        from app.routes.auth import AuthPayload, auth_join
        from fastapi import Response

        db = self.SessionLocal()
        try:
            response = Response()
            result = auth_join(AuthPayload(email="new@example.com", password="Secret123"), response, db)
            self.assertTrue(result["joined"])
            user = db.query(User).filter(User.email == "new@example.com").first()
            self.assertTrue(user.password_hash.startswith("pbkdf2_sha256$"))
        finally:
            db.close()

    def test_legacy_sha256_user_upgrades_on_login(self):
        import hashlib

        from app.models import User
        from app.routes.auth import AuthPayload, auth_login
        from fastapi import Response

        db = self.SessionLocal()
        try:
            legacy_hash = hashlib.sha256("Legacy123".encode("utf-8")).hexdigest()
            user = User(email="legacy@example.com", password_hash=legacy_hash, role="member")
            db.add(user)
            db.commit()
            db.refresh(user)

            response = Response()
            result = auth_login(AuthPayload(email="legacy@example.com", password="Legacy123"), response, db)
            self.assertTrue(result["authenticated"])

            db.refresh(user)
            self.assertNotEqual(user.password_hash, legacy_hash)
            self.assertTrue(user.password_hash.startswith("pbkdf2_sha256$"))
        finally:
            db.close()

    def test_incorrect_password_fails(self):
        from fastapi import HTTPException, Response

        from app.routes.auth import AuthPayload, auth_join, auth_login

        db = self.SessionLocal()
        try:
            auth_join(AuthPayload(email="wrongpass@example.com", password="RightPass123"), Response(), db)
            with self.assertRaises(HTTPException) as context:
                auth_login(AuthPayload(email="wrongpass@example.com", password="WrongPass123"), Response(), db)
            self.assertEqual(context.exception.status_code, 401)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
