import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.session import build_session_cookie_value

REPO_ROOT = Path(__file__).resolve().parents[2]


class AuthCredentialWiringPhase7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_auth_credential_wiring_phase7.db')
        if db_path.exists():
            db_path.unlink()
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['SESSION_SECRET'] = 'test-session-secret'

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine
        from app.main import app

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal
        cls.client = TestClient(app)

    def setUp(self):
        from app.authz import seed_rbac_defaults
        from app.models import User
        from app.security import hash_password

        with self.SessionLocal() as db:
            db.query(User).delete()
            db.commit()

            self.admin_email = 'phase7-admin@example.com'
            self.admin_password = 'password123'
            admin = User(email=self.admin_email, password_hash=hash_password(self.admin_password), role='admin')
            member = User(email='phase7-member@example.com', password_hash=hash_password('password123'), role='member')
            db.add_all([admin, member])
            db.commit()
            seed_rbac_defaults(db)
            self.admin_id = admin.id
            self.member_id = member.id

    def test_audiobook_signed_cookie_resolves_real_authenticated_user(self):
        from starlette.requests import Request
        from app.models import User
        from app.routes.audiobook import _resolve_session_user

        def _request_with_cookie(cookie_value: str) -> Request:
            scope = {
                'type': 'http',
                'method': 'GET',
                'path': '/audiobooks',
                'headers': [(b'cookie', f'mufasa_session={cookie_value}'.encode('utf-8'))],
            }
            return Request(scope)

        with self.SessionLocal() as db:
            admin_user = _resolve_session_user(_request_with_cookie(build_session_cookie_value(self.admin_id)), db)
            member_user = _resolve_session_user(_request_with_cookie(build_session_cookie_value(self.member_id)), db)

            self.assertIsNotNone(admin_user)
            self.assertIsNotNone(member_user)
            self.assertEqual(admin_user.id, self.admin_id)
            self.assertEqual(member_user.id, self.member_id)

            guest = db.query(User).filter(User.email == 'pilot.audiobook.guest@local').first()
            self.assertIsNone(guest)

    def test_admin_overview_and_activity_work_after_login_signed_session(self):
        # Use explicit login path to validate the normal browser flow.
        login = self.client.post('/auth/login', json={'email': self.admin_email, 'password': self.admin_password})
        self.assertEqual(login.status_code, 200)

        login_cookie = login.cookies.get('mufasa_session')
        self.assertTrue(login_cookie)

        # login -> /auth/me -> admin overview -> activity stream
        cookies = {'mufasa_session': login_cookie}
        me = self.client.get('/auth/me', cookies=cookies)
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.json().get('authenticated'))

        overview = self.client.get('/admin/ai/overview', cookies=cookies)
        self.assertEqual(overview.status_code, 200)

        activity = self.client.get('/admin/activity-stream', cookies=cookies)
        self.assertEqual(activity.status_code, 200)


class FrontendCredentialWiringStaticTests(unittest.TestCase):
    def test_assessment_service_fetches_include_credentials(self):
        src = (REPO_ROOT / 'src/services/leadershipService.js').read_text()
        self.assertIn('assessment/submit', src)
        self.assertIn('credentials: "include"', src)
        self.assertIn('assessment/results/${encodeURIComponent(userId)}', src)
        self.assertIn('assessment/dashboard/${encodeURIComponent(userId)}', src)

    def test_system_verification_uses_shared_api_client(self):
        src = (REPO_ROOT / 'src/pages/SystemVerificationPage.jsx').read_text()
        self.assertIn('import { api } from "../api/api";', src)
        self.assertIn('api("/system/verification/full"', src)


if __name__ == '__main__':
    unittest.main()
