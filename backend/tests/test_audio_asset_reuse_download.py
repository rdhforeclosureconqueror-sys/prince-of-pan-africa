import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class AudioAssetReuseDownloadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_audio_asset_reuse_download.db')
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
        from app.models import AudioAsset, Audiobook, AudiobookChapter, AudiobookProgress, User
        from app.routes.chat import STATIC_AUDIO_DIR
        from app.security import hash_password

        with self.SessionLocal() as db:
            db.query(AudiobookProgress).delete()
            db.query(AudiobookChapter).delete()
            db.query(Audiobook).delete()
            db.query(AudioAsset).delete()
            db.query(User).delete()
            db.commit()

            user = User(email='audio-owner@example.com', password_hash=hash_password('password123'), role='member')
            db.add(user)
            db.commit()
            seed_rbac_defaults(db)

        self.audio_path = STATIC_AUDIO_DIR / 'reuse-test.mp3'
        self.audio_path.parent.mkdir(parents=True, exist_ok=True)
        self.audio_path.write_bytes(b'ID3\x04\x00\x00\x00\x00\x00\x00test-audio')

    def _authed_client(self):
        cookie_res = self.client.post('/auth/login', json={'email': 'audio-owner@example.com', 'password': 'password123'})
        self.assertEqual(cookie_res.status_code, 200)
        client = TestClient(self.client.app)
        client.cookies.set('mufasa_session', cookie_res.cookies.get('mufasa_session'))
        return client

    def _create_draft_book(self, client):
        created = client.post('/audiobooks/create', json={
            'title': 'Al Andalus',
            'author': 'A',
            'text': 'When the Moors entered Europe. Knowledge moved through cities.',
            'voice': 'alloy',
            'generate_audio': False,
        })
        self.assertEqual(created.status_code, 200)
        book = created.json()['audiobook']
        return book, book['chapters'][0]

    def test_save_retrieve_download_and_reuse_without_provider_call(self):
        import app.routes.audiobook as audiobook_routes

        client = self._authed_client()
        book, chapter = self._create_draft_book(client)
        audio_url = f'http://testserver/static/audio/{self.audio_path.name}'

        saved = client.post('/api/audio/save', json={
            'bookId': book['id'],
            'chapterId': chapter['id'],
            'title': chapter['title'],
            'voice': 'alloy',
            'model': 'alloy',
            'duration': 12,
            'format': 'mp3',
            'audioUrl': audio_url,
        })
        self.assertEqual(saved.status_code, 200)
        saved_audio = saved.json()['audio']
        self.assertEqual(saved_audio['format'], 'mp3')
        self.assertEqual(saved_audio['storageKey'], 'audio/reuse-test.mp3')

        retrieved = client.get(f"/api/audio/book/{book['id']}/chapter/{chapter['id']}")
        self.assertEqual(retrieved.status_code, 200)
        self.assertIn('Use saved audio or regenerate', retrieved.json()['message'])

        download = client.get(f"/api/audio/download/{saved_audio['id']}")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.headers['content-type'].split(';')[0], 'audio/mpeg')
        self.assertIn('attachment;', download.headers['content-disposition'])
        self.assertIn('al-andalus-chapter-01-chapter-1.mp3', download.headers['content-disposition'])

        original_generate = audiobook_routes.generate_tts_audio_url

        def fail_if_provider_path_is_used(**kwargs):
            raise AssertionError('provider should not be called when saved audio exists')

        audiobook_routes.generate_tts_audio_url = fail_if_provider_path_is_used
        try:
            reused = client.post(f"/audiobooks/{book['id']}/chapters/{chapter['chapter_index']}/generate")
        finally:
            audiobook_routes.generate_tts_audio_url = original_generate

        self.assertEqual(reused.status_code, 200)
        self.assertFalse(reused.json()['provider_called'])
        self.assertEqual(reused.json()['default_action'], 'use_saved_audio')


if __name__ == '__main__':
    unittest.main()
