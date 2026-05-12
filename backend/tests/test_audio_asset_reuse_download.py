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

            owner = User(email='audio-owner@example.com', password_hash=hash_password('password123'), role='member')
            other = User(email='audio-other@example.com', password_hash=hash_password('password123'), role='member')
            db.add_all([owner, other])
            db.commit()
            seed_rbac_defaults(db)

        self.audio_path = STATIC_AUDIO_DIR / 'reuse-test.mp3'
        self.audio_path.parent.mkdir(parents=True, exist_ok=True)
        self.audio_path.write_bytes(b'ID3\x04\x00\x00\x00\x00\x00\x00test-audio')

    def _authed_client(self, email='audio-owner@example.com'):
        cookie_res = self.client.post('/auth/login', json={'email': email, 'password': 'password123'})
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

    def _saved_audio(self, client):
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
        return book, chapter, saved.json()['audio']

    def test_save_retrieve_download_and_reuse_without_provider_call(self):
        import app.routes.audiobook as audiobook_routes

        client = self._authed_client()
        book, chapter, saved_audio = self._saved_audio(client)
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
        self.assertTrue(download.content.startswith(b'ID3'))

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

    def test_audio_download_requires_auth(self):
        owner_client = self._authed_client()
        _book, _chapter, saved_audio = self._saved_audio(owner_client)

        res = TestClient(self.client.app).get(f"/api/audio/download/{saved_audio['id']}")

        self.assertEqual(res.status_code, 401)

    def test_non_owner_cannot_download_another_users_audio(self):
        owner_client = self._authed_client()
        _book, _chapter, saved_audio = self._saved_audio(owner_client)
        other_client = self._authed_client('audio-other@example.com')

        res = other_client.get(f"/api/audio/download/{saved_audio['id']}")

        self.assertEqual(res.status_code, 404)

    def test_missing_audio_file_returns_clear_404(self):
        owner_client = self._authed_client()
        _book, _chapter, saved_audio = self._saved_audio(owner_client)
        self.audio_path.unlink()

        res = owner_client.get(f"/api/audio/download/{saved_audio['id']}")

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['detail'], 'Audio file is missing from storage. Please regenerate this chapter.')

    def test_incomplete_generation_returns_409(self):
        from app.models import AudiobookChapter

        owner_client = self._authed_client()
        _book, chapter, saved_audio = self._saved_audio(owner_client)
        with self.SessionLocal() as db:
            db.query(AudiobookChapter).filter(AudiobookChapter.id == chapter['id']).update({'status': 'generating'})
            db.commit()

        res = owner_client.get(f"/api/audio/download/{saved_audio['id']}")

        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()['detail'], 'Audio generation is not complete for this chapter yet.')

    def test_audio_download_path_traversal_storage_key_returns_404(self):
        from app.models import AudioAsset

        owner_client = self._authed_client()
        _book, _chapter, saved_audio = self._saved_audio(owner_client)
        with self.SessionLocal() as db:
            db.query(AudioAsset).filter(AudioAsset.id == saved_audio['id']).update({'storage_key': 'audio/../secret.mp3'})
            db.commit()

        res = owner_client.get(f"/api/audio/download/{saved_audio['id']}")

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['detail'], 'Audio file is missing from storage. Please regenerate this chapter.')

    def test_signed_in_user_without_audio_permission_gets_403(self):
        from app.models import Permission, Role

        with self.SessionLocal() as db:
            member = db.query(Role).filter(Role.name == 'member').first()
            permission = db.query(Permission).filter(Permission.name == 'audiobook:read_self').first()
            self.assertIsNotNone(member)
            self.assertIsNotNone(permission)
            if permission in member.permissions:
                member.permissions.remove(permission)
            db.commit()

        res = self._authed_client().get('/api/audio/download/1')

        self.assertEqual(res.status_code, 403)


if __name__ == '__main__':
    unittest.main()
