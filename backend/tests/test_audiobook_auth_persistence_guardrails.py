import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class AudiobookAuthPersistenceGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_audiobook_auth_persistence_guardrails.db')
        if db_path.exists():
            db_path.unlink()

        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        os.environ['SESSION_SECRET'] = 'test-session-secret'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['ALLOW_GUEST_AUDIOBOOKS'] = 'false'

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine
        from app.main import app

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal
        cls.client = TestClient(app)

    def setUp(self):
        from app.authz import seed_rbac_defaults
        from app.models import AudioAsset, Audiobook, AudiobookChapter, AudiobookChapterReflection, AudiobookProgress, User
        from app.security import hash_password

        with self.SessionLocal() as db:
            db.query(AudiobookChapterReflection).delete()
            db.query(AudiobookProgress).delete()
            db.query(AudiobookChapter).delete()
            db.query(Audiobook).delete()
            db.query(AudioAsset).delete()
            db.query(User).delete()
            db.commit()

            u1 = User(email='owner1@example.com', password_hash=hash_password('password123'), role='member')
            u2 = User(email='owner2@example.com', password_hash=hash_password('password123'), role='member')
            db.add_all([u1, u2])
            db.commit()
            seed_rbac_defaults(db)

    def _login_cookie(self, email: str) -> str:
        res = self.client.post('/auth/login', json={'email': email, 'password': 'password123'})
        self.assertEqual(res.status_code, 200)
        cookie = res.cookies.get('mufasa_session')
        self.assertTrue(cookie)
        return cookie

    def test_unauthenticated_production_audiobook_list_returns_401(self):
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['ALLOW_GUEST_AUDIOBOOKS'] = 'false'
        try:
            res = TestClient(self.client.app).get('/audiobooks')
            self.assertEqual(res.status_code, 401)
        finally:
            os.environ['ENVIRONMENT'] = 'test'

    def test_unauthenticated_production_reflection_summary_returns_401(self):
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['ALLOW_GUEST_AUDIOBOOKS'] = 'false'
        try:
            res = TestClient(self.client.app).post('/audiobooks/1/reflections/summary', json={'include_skipped': False})
            self.assertEqual(res.status_code, 401)
        finally:
            os.environ['ENVIRONMENT'] = 'test'

    def test_authenticated_user_sees_only_own_books(self):
        c1 = self._login_cookie('owner1@example.com')
        user1_client = TestClient(self.client.app)
        user1_client.cookies.set('mufasa_session', c1)

        c2 = self._login_cookie('owner2@example.com')
        user2_client = TestClient(self.client.app)
        user2_client.cookies.set('mufasa_session', c2)

        r1 = user1_client.post('/audiobooks/create', json={
            'title': 'User1 Book', 'author': 'A', 'text': 'chapter one text', 'generate_audio': False,
        })
        self.assertEqual(r1.status_code, 200)

        r2 = user2_client.post('/audiobooks/create', json={
            'title': 'User2 Book', 'author': 'B', 'text': 'different text', 'generate_audio': False,
        })
        self.assertEqual(r2.status_code, 200)

        list1 = user1_client.get('/audiobooks')
        list2 = user2_client.get('/audiobooks')
        self.assertEqual(list1.status_code, 200)
        self.assertEqual(list2.status_code, 200)
        self.assertEqual(len(list1.json()['items']), 1)
        self.assertEqual(len(list2.json()['items']), 1)
        self.assertEqual(list1.json()['items'][0]['title'], 'User1 Book')
        self.assertEqual(list2.json()['items'][0]['title'], 'User2 Book')

    def test_book_and_progress_persist_under_authenticated_user_id(self):
        from app.models import Audiobook, AudiobookProgress, User

        cookie = self._login_cookie('owner1@example.com')
        authed_client = TestClient(self.client.app)
        authed_client.cookies.set('mufasa_session', cookie)
        created = authed_client.post('/audiobooks/create', json={
            'title': 'Progress Book', 'author': 'A', 'text': 'progress text', 'generate_audio': False,
        })
        self.assertEqual(created.status_code, 200)
        book_id = created.json()['audiobook']['id']

        progress = authed_client.post(f'/audiobooks/{book_id}/progress', json={
            'chapter_index': 1, 'position_seconds': 42, 'playback_rate': '1.25', 'completed_chapters': [1],
        })
        self.assertEqual(progress.status_code, 200)

        with self.SessionLocal() as db:
            user = db.query(User).filter(User.email == 'owner1@example.com').first()
            book = db.query(Audiobook).filter(Audiobook.id == book_id).first()
            prog = db.query(AudiobookProgress).filter(AudiobookProgress.audiobook_id == book_id).first()
            self.assertEqual(book.user_id, user.id)
            self.assertEqual(prog.user_id, user.id)
            self.assertEqual(prog.position_seconds, 42)

    def test_generation_status_surfaces_failed_chapter_details(self):
        from app.models import AudiobookChapter

        cookie = self._login_cookie('owner1@example.com')
        authed_client = TestClient(self.client.app)
        authed_client.cookies.set('mufasa_session', cookie)
        created = authed_client.post('/audiobooks/create', json={
            'title': 'Failed Chapter Book', 'author': 'A', 'text': 'failed chapter text', 'generate_audio': False,
        })
        self.assertEqual(created.status_code, 200)
        book_id = created.json()['audiobook']['id']
        chapter_id = created.json()['audiobook']['chapters'][0]['id']

        with self.SessionLocal() as db:
            db.query(AudiobookChapter).filter(AudiobookChapter.id == chapter_id).update({'status': 'failed'})
            db.commit()

        status = authed_client.get(f'/audiobooks/{book_id}/generation-status')

        self.assertEqual(status.status_code, 200)
        progress = status.json()['generation_progress']
        self.assertEqual(progress['failed_chapters'], 1)
        self.assertEqual(progress['failed_chapter_indexes'], [1])
        self.assertEqual(progress['failed_chapter_errors'][0]['chapter_index'], 1)
        self.assertIn('Chapter generation failed', progress['failed_chapter_errors'][0]['message'])


if __name__ == '__main__':
    unittest.main()
