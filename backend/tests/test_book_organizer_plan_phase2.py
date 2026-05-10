import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class BookOrganizerPlanPhase2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_book_organizer_plan_phase2.db')
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
        from app.models import BookOrganizationPlan, BookOrganizerBlock, BookOrganizerDocument, User, UserRole
        from app.security import hash_password
        from app.config import settings

        settings.ENABLE_TEXT_BOOK_ORGANIZER = True

        with self.SessionLocal() as db:
            db.query(BookOrganizationPlan).delete()
            db.query(BookOrganizerBlock).delete()
            db.query(BookOrganizerDocument).delete()
            db.query(UserRole).delete()
            db.query(User).delete()
            db.commit()

            u1 = User(email='organizer1@example.com', password_hash=hash_password('password123'), role='subscriber')
            db.add(u1)
            db.commit()

            from app.authz import seed_rbac_defaults
            seed_rbac_defaults(db)

    def _authed_client(self) -> TestClient:
        res = self.client.post('/auth/login', json={'email': 'organizer1@example.com', 'password': 'password123'})
        self.assertEqual(res.status_code, 200)
        cookie = res.cookies.get('mufasa_session')
        client = TestClient(self.client.app)
        client.cookies.set('mufasa_session', cookie)
        return client

    def _create_document(self, client: TestClient, text: str = 'A\n\nB\n\nC\n\nD\n\nE\n\nF') -> int:
        res = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Source Title', 'text': text})
        self.assertEqual(res.status_code, 200)
        return res.json()['document']['id']

    def test_proposal_uses_only_existing_ids_and_includes_all_once(self):
        client = self._authed_client()
        document_id = self._create_document(client)

        res = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id, 'plan_name': 'P1'})
        self.assertEqual(res.status_code, 200)
        payload = res.json()

        chapter_ids = []
        for chapter in payload['structure']['chapters']:
            chapter_ids.extend(chapter['block_ids'])

        self.assertEqual(chapter_ids, ['p00001', 'p00002', 'p00003', 'p00004', 'p00005', 'p00006'])
        self.assertEqual(len(chapter_ids), len(set(chapter_ids)))
        self.assertEqual(payload['structure']['warnings'], [])

    def test_explicit_unused_blocks_are_warned_and_excluded(self):
        client = self._authed_client()
        document_id = self._create_document(client)

        res = client.post(
            '/audiobooks/organizer/propose-plan',
            json={'document_id': document_id, 'unused_block_ids': ['p00006']},
        )
        self.assertEqual(res.status_code, 200)
        payload = res.json()

        chapter_ids = []
        for chapter in payload['structure']['chapters']:
            chapter_ids.extend(chapter['block_ids'])

        self.assertNotIn('p00006', chapter_ids)
        self.assertEqual(payload['structure']['warnings'][0]['block_ids'], ['p00006'])

    def test_plan_persistence_and_no_body_text_in_structure(self):
        from app.models import BookOrganizationPlan

        client = self._authed_client()
        document_id = self._create_document(client)
        res = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id, 'plan_name': 'Saved Plan'})
        self.assertEqual(res.status_code, 200)
        plan_id = res.json()['plan_id']

        with self.SessionLocal() as db:
            plan = db.query(BookOrganizationPlan).filter(BookOrganizationPlan.id == plan_id).first()
            self.assertIsNotNone(plan)
            self.assertEqual(plan.name, 'Saved Plan')
            self.assertIn('title_candidate', plan.structure)
            serialized = str(plan.structure)
            self.assertNotIn('A', serialized)
            self.assertNotIn('B', serialized)

    def test_invalid_block_ids_rejected(self):
        client = self._authed_client()
        document_id = self._create_document(client)

        res = client.post(
            '/audiobooks/organizer/propose-plan',
            json={'document_id': document_id, 'unused_block_ids': ['p99999']},
        )
        self.assertEqual(res.status_code, 422)

    def test_preview_returns_original_paragraph_text_grouped_by_chapter(self):
        client = self._authed_client()
        document_id = self._create_document(client, text='Para A\n\nPara B\n\nPara C')

        plan = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id}).json()
        preview = client.post('/audiobooks/organizer/preview', json={'document_id': document_id, 'plan_id': plan['plan_id']})
        self.assertEqual(preview.status_code, 200)

        payload = preview.json()
        self.assertEqual(payload['document_id'], document_id)
        chapter_paragraphs = [p['text'] for ch in payload['chapters'] for p in ch['paragraphs']]
        self.assertEqual(chapter_paragraphs, ['Para A', 'Para B', 'Para C'])

    def test_preview_rejects_missing_plan_block_ids_with_422(self):
        from app.models import BookOrganizationPlan

        client = self._authed_client()
        document_id = self._create_document(client, text='Para A\n\nPara B')
        plan_res = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id})
        self.assertEqual(plan_res.status_code, 200)
        plan_id = plan_res.json()['plan_id']

        with self.SessionLocal() as db:
            plan = db.query(BookOrganizationPlan).filter(BookOrganizationPlan.id == plan_id).first()
            structure = dict(plan.structure)
            chapters = [dict(ch) for ch in structure['chapters']]
            first = dict(chapters[0])
            first['block_ids'] = [*first['block_ids'], 'p99999']
            chapters[0] = first
            structure['chapters'] = chapters
            plan.structure = structure
            db.add(plan)
            db.commit()

        preview = client.post('/audiobooks/organizer/preview', json={'document_id': document_id, 'plan_id': plan_id})
        self.assertEqual(preview.status_code, 422)
        self.assertEqual(preview.json()['detail']['invalid_block_ids'], ['p99999'])


if __name__ == '__main__':
    unittest.main()
