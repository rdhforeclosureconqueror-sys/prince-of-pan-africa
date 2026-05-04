import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class BookOrganizerTextIngestionPhase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_book_organizer_text_ingestion_phase1.db')
        if db_path.exists():
            db_path.unlink()

        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        os.environ['SESSION_SECRET'] = 'test-session-secret'
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['ENABLE_TEXT_BOOK_ORGANIZER'] = 'true'

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine
        from app.main import app

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal
        cls.client = TestClient(app)

    def setUp(self):
        from app.models import BookOrganizationPlan, BookOrganizerBlock, BookOrganizerDocument, User
        from app.security import hash_password
        from app.config import settings

        settings.ENABLE_TEXT_BOOK_ORGANIZER = True

        with self.SessionLocal() as db:
            db.query(BookOrganizationPlan).delete()
            db.query(BookOrganizerBlock).delete()
            db.query(BookOrganizerDocument).delete()
            db.query(User).delete()
            db.commit()

            u1 = User(email='organizer1@example.com', password_hash=hash_password('password123'), role='member')
            u2 = User(email='organizer2@example.com', password_hash=hash_password('password123'), role='member')
            db.add_all([u1, u2])
            db.commit()

    def _authed_client(self, email: str) -> TestClient:
        res = self.client.post('/auth/login', json={'email': email, 'password': 'password123'})
        self.assertEqual(res.status_code, 200)
        cookie = res.cookies.get('mufasa_session')
        client = TestClient(self.client.app)
        client.cookies.set('mufasa_session', cookie)
        return client

    def test_feature_flag_off_rejects_endpoint(self):
        from app.config import settings

        settings.ENABLE_TEXT_BOOK_ORGANIZER = False
        try:
            authed = self._authed_client('organizer1@example.com')
            res = authed.post('/audiobooks/organizer/ingest-text', json={'title': 'Flag Off', 'text': 'Para 1'})
            self.assertEqual(res.status_code, 404)
        finally:
            settings.ENABLE_TEXT_BOOK_ORGANIZER = True

    def test_auth_required_for_text_ingestion(self):
        res = self.client.post('/audiobooks/organizer/ingest-text', json={'title': 'No Auth', 'text': 'Para 1'})
        self.assertEqual(res.status_code, 401)

    def test_pasted_text_creates_document_and_blocks(self):
        from app.models import BookOrganizerBlock, BookOrganizerDocument, User

        source_text = 'First paragraph.\nLine two.\n\nSecond paragraph.\n\nThird paragraph.'
        authed = self._authed_client('organizer1@example.com')
        res = authed.post('/audiobooks/organizer/ingest-text', json={'title': 'My Notes', 'text': source_text})
        self.assertEqual(res.status_code, 200)

        payload = res.json()
        self.assertEqual(payload['document']['title'], 'My Notes')
        self.assertEqual(len(payload['blocks']), 3)
        self.assertEqual([b['block_id'] for b in payload['blocks']], ['p00001', 'p00002', 'p00003'])

        with self.SessionLocal() as db:
            user = db.query(User).filter(User.email == 'organizer1@example.com').first()
            doc = db.query(BookOrganizerDocument).filter(BookOrganizerDocument.id == payload['document']['id']).first()
            blocks = db.query(BookOrganizerBlock).filter(BookOrganizerBlock.document_id == doc.id).order_by(BookOrganizerBlock.block_index.asc()).all()
            self.assertEqual(doc.user_id, user.id)
            expected_paragraphs = ['First paragraph.\nLine two.', 'Second paragraph.', 'Third paragraph.']
            self.assertEqual([b.text for b in blocks], expected_paragraphs)

    def test_checksums_match_stored_text(self):
        from app.models import BookOrganizerBlock, compute_text_checksum

        authed = self._authed_client('organizer1@example.com')
        res = authed.post('/audiobooks/organizer/ingest-text', json={'title': 'Checksum', 'text': 'Alpha\n\nBeta'})
        self.assertEqual(res.status_code, 200)

        document_id = res.json()['document']['id']
        with self.SessionLocal() as db:
            blocks = db.query(BookOrganizerBlock).filter(BookOrganizerBlock.document_id == document_id).order_by(BookOrganizerBlock.block_index.asc()).all()
            self.assertEqual(len(blocks), 2)
            for block in blocks:
                self.assertEqual(block.checksum, compute_text_checksum(block.text))

    def test_empty_and_oversized_text_rejected(self):
        authed = self._authed_client('organizer1@example.com')

        empty = authed.post('/audiobooks/organizer/ingest-text', json={'title': 'Empty', 'text': '   \n\n   '})
        self.assertEqual(empty.status_code, 422)

        oversized_text = 'x' * 1_200_001
        oversized = authed.post('/audiobooks/organizer/ingest-text', json={'title': 'Huge', 'text': oversized_text})
        self.assertIn(oversized.status_code, {413, 422})


if __name__ == '__main__':
    unittest.main()
