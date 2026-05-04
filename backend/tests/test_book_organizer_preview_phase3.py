import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class BookOrganizerPreviewPhase3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_book_organizer_preview_phase3.db')
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
        from app.config import settings
        from app.models import BookOrganizationPlan, BookOrganizerBlock, BookOrganizerDocument, User
        from app.security import hash_password

        settings.ENABLE_TEXT_BOOK_ORGANIZER = True

        with self.SessionLocal() as db:
            db.query(BookOrganizationPlan).delete()
            db.query(BookOrganizerBlock).delete()
            db.query(BookOrganizerDocument).delete()
            db.query(User).delete()
            db.commit()

            u1 = User(email='organizer3@example.com', password_hash=hash_password('password123'), role='member')
            u2 = User(email='organizer4@example.com', password_hash=hash_password('password123'), role='member')
            db.add(u1)
            db.add(u2)
            db.commit()

    def _authed_client(self, email: str = 'organizer3@example.com') -> TestClient:
        res = self.client.post('/auth/login', json={'email': email, 'password': 'password123'})
        self.assertEqual(res.status_code, 200)
        cookie = res.cookies.get('mufasa_session')
        client = TestClient(self.client.app)
        client.cookies.set('mufasa_session', cookie)
        return client

    def _ingest_and_plan(self, client: TestClient, text: str = 'A1\n\nA2\n\nA3\n\nA4\n\nA5\n\nA6'):
        ingest = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Source Title', 'text': text})
        self.assertEqual(ingest.status_code, 200)
        document_id = ingest.json()['document']['id']

        plan = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id, 'plan_name': 'P3'})
        self.assertEqual(plan.status_code, 200)
        return document_id, plan.json()['plan_id'], ingest.json()['blocks']

    def test_preview_uses_only_immutable_stored_block_text_and_matches_exactly(self):
        client = self._authed_client()
        _, plan_id, blocks = self._ingest_and_plan(client)

        preview = client.post('/audiobooks/organizer/preview', json={'plan_id': plan_id})
        self.assertEqual(preview.status_code, 200)
        payload = preview.json()

        first_chapter_paragraphs = payload['chapters'][0]['paragraphs']
        self.assertEqual(first_chapter_paragraphs, ['A1', 'A2', 'A3', 'A4', 'A5'])
        self.assertEqual(payload['warnings'], [])
        self.assertEqual([b['block_id'] for b in blocks], ['p00001', 'p00002', 'p00003', 'p00004', 'p00005', 'p00006'])

    def test_invalid_block_reference_fails(self):
        from app.models import BookOrganizationPlan

        client = self._authed_client()
        _, plan_id, _ = self._ingest_and_plan(client)

        with self.SessionLocal() as db:
            plan = db.query(BookOrganizationPlan).filter(BookOrganizationPlan.id == plan_id).first()
            structure = dict(plan.structure)
            chapters = [dict(ch) for ch in structure['chapters']]
            first = dict(chapters[0])
            first['block_ids'] = ['p99999', *first['block_ids'][1:]]
            chapters[0] = first
            structure['chapters'] = chapters
            plan.structure = structure
            db.add(plan)
            db.commit()

        preview = client.post('/audiobooks/organizer/preview', json={'plan_id': plan_id})
        self.assertEqual(preview.status_code, 422)

    def test_checksum_mismatch_fails(self):
        from sqlalchemy import text

        client = self._authed_client()
        _, plan_id, _ = self._ingest_and_plan(client)

        with self.SessionLocal() as db:
            db.execute(text("UPDATE book_organizer_blocks SET checksum = :checksum WHERE block_id = 'p00001'"), {'checksum': '0' * 64})
            db.commit()

        preview = client.post('/audiobooks/organizer/preview', json={'plan_id': plan_id})
        self.assertEqual(preview.status_code, 422)

    def test_same_plan_produces_same_preview(self):
        client = self._authed_client()
        _, plan_id, _ = self._ingest_and_plan(client)

        preview1 = client.post('/audiobooks/organizer/preview', json={'plan_id': plan_id})
        preview2 = client.post('/audiobooks/organizer/preview', json={'plan_id': plan_id})
        self.assertEqual(preview1.status_code, 200)
        self.assertEqual(preview2.status_code, 200)
        self.assertEqual(preview1.json(), preview2.json())

    def test_plan_must_belong_to_user(self):
        owner_client = self._authed_client('organizer3@example.com')
        _, plan_id, _ = self._ingest_and_plan(owner_client)

        other_client = self._authed_client('organizer4@example.com')
        preview = other_client.post('/audiobooks/organizer/preview', json={'plan_id': plan_id})
        self.assertEqual(preview.status_code, 404)


if __name__ == '__main__':
    unittest.main()
