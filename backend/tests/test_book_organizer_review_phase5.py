import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class BookOrganizerReviewPhase5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_book_organizer_review_phase5.db')
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
            db.add(User(email='organizer1@example.com', password_hash=hash_password('password123'), role='member'))
            db.commit()

    def _authed_client(self):
        res = self.client.post('/auth/login', json={'email': 'organizer1@example.com', 'password': 'password123'})
        cookie = res.cookies.get('mufasa_session')
        client = TestClient(self.client.app)
        client.cookies.set('mufasa_session', cookie)
        return client

    def _doc_and_plan(self, client):
        ingest = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Source', 'text': 'A\n\nB\n\nC\n\nD\n\nE\n\nF'}).json()
        plan = client.post('/audiobooks/organizer/propose-plan', json={'document_id': ingest['document']['id']}).json()
        return ingest['document']['id'], plan['plan_id']

    def test_rename_changes_chapter_title_only(self):
        client = self._authed_client()
        document_id, plan_id = self._doc_and_plan(client)
        edited = client.post('/audiobooks/organizer/review-structure', json={
            'document_id': document_id,
            'plan_id': plan_id,
            'chapter_title_overrides': {'1': 'Renamed Chapter'},
        })
        self.assertEqual(edited.status_code, 200)
        chapters = edited.json()['structure']['chapters']
        self.assertEqual(chapters[0]['chapter_title'], 'Renamed Chapter')
        self.assertEqual([b for c in chapters for b in c['block_ids']], ['p00001', 'p00002', 'p00003', 'p00004', 'p00005', 'p00006'])

    def test_merge_preserves_block_ids_order(self):
        client = self._authed_client()
        document_id, plan_id = self._doc_and_plan(client)
        edited = client.post('/audiobooks/organizer/review-structure', json={
            'document_id': document_id,
            'plan_id': plan_id,
            'merge_chapter_indexes': [1],
        }).json()
        merged_ids = [b for c in edited['structure']['chapters'] for b in c['block_ids']]
        self.assertEqual(merged_ids, ['p00001', 'p00002', 'p00003', 'p00004', 'p00005', 'p00006'])

    def test_split_preserves_block_ids_order(self):
        client = self._authed_client()
        document_id, plan_id = self._doc_and_plan(client)
        edited = client.post('/audiobooks/organizer/review-structure', json={
            'document_id': document_id,
            'plan_id': plan_id,
            'split_operations': [{'chapter_index': 1, 'boundary_block_id': 'p00003'}],
        }).json()
        split_ids = [b for c in edited['structure']['chapters'] for b in c['block_ids']]
        self.assertEqual(split_ids, ['p00001', 'p00002', 'p00003', 'p00004', 'p00005', 'p00006'])

    def test_preview_body_matches_original_blocks(self):
        client = self._authed_client()
        ingest = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Source', 'text': 'Para 1\n\nPara 2\n\nPara 3'})
        document_id = ingest.json()['document']['id']
        plan_id = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id}).json()['plan_id']
        revised = client.post('/audiobooks/organizer/review-structure', json={
            'document_id': document_id,
            'plan_id': plan_id,
            'chapter_title_overrides': {'1': 'New Name'},
        }).json()
        preview = client.post('/audiobooks/organizer/preview', json={'document_id': document_id, 'plan_id': revised['plan_id']}).json()
        self.assertEqual([p['text'] for c in preview['chapters'] for p in c['paragraphs']], ['Para 1', 'Para 2', 'Para 3'])

    def test_invalid_block_ids_fail_hard(self):
        from app.models import BookOrganizationPlan

        client = self._authed_client()
        document_id, plan_id = self._doc_and_plan(client)
        with self.SessionLocal() as db:
            plan = db.query(BookOrganizationPlan).filter(BookOrganizationPlan.id == plan_id).first()
            structure = dict(plan.structure)
            chapters = [dict(ch) for ch in structure['chapters']]
            chapters[0]['block_ids'] = ['p99999']
            structure['chapters'] = chapters
            plan.structure = structure
            db.commit()

        edited = client.post('/audiobooks/organizer/review-structure', json={'document_id': document_id, 'plan_id': plan_id})
        self.assertEqual(edited.status_code, 422)


if __name__ == '__main__':
    unittest.main()
