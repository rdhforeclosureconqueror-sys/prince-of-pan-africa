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
        from app.models import BookOrganizationPlan, BookOrganizerBlock, BookOrganizerDocument, User, UserRole
        from app.security import hash_password

        settings.ENABLE_TEXT_BOOK_ORGANIZER = True

        with self.SessionLocal() as db:
            db.query(BookOrganizationPlan).delete()
            db.query(BookOrganizerBlock).delete()
            db.query(BookOrganizerDocument).delete()
            db.query(UserRole).delete()
            db.query(User).delete()
            db.commit()
            db.add(User(email='organizer1@example.com', password_hash=hash_password('password123'), role='subscriber'))
            db.commit()

            from app.authz import seed_rbac_defaults
            seed_rbac_defaults(db)

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
            structure['approved'] = True
            structure['review_status'] = 'approved'
            plan.structure = structure
            db.commit()

        edited = client.post('/audiobooks/organizer/review-structure', json={'document_id': document_id, 'plan_id': plan_id})
        self.assertEqual(edited.status_code, 422)

    def test_export_txt_uses_original_block_text_only(self):
        client = self._authed_client()
        ingest = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Source', 'text': 'Para 1\n\nPara 2\n\nPara 3'})
        document_id = ingest.json()['document']['id']
        plan_id = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id}).json()['plan_id']
        revised = client.post('/audiobooks/organizer/review-structure', json={
            'document_id': document_id,
            'plan_id': plan_id,
            'chapter_title_overrides': {'1': 'Renamed'},
        }).json()
        exported = client.post('/audiobooks/organizer/export-txt', json={'document_id': document_id, 'plan_id': revised['plan_id']})
        self.assertEqual(exported.status_code, 200)
        body = exported.text
        self.assertIn('Renamed', body)
        self.assertIn('Para 1', body)
        self.assertIn('Para 2', body)
        self.assertIn('Para 3', body)
        self.assertNotIn('p00001', body)

    def test_export_txt_fails_on_checksum_mismatch(self):
        from app.models import BookOrganizerBlock

        client = self._authed_client()
        document_id, plan_id = self._doc_and_plan(client)
        revised = client.post('/audiobooks/organizer/review-structure', json={'document_id': document_id, 'plan_id': plan_id}).json()
        with self.SessionLocal() as db:
            block = db.query(BookOrganizerBlock).filter(BookOrganizerBlock.document_id == document_id, BookOrganizerBlock.block_id == 'p00001').first()
            db.execute(
                BookOrganizerBlock.__table__.update().where(BookOrganizerBlock.id == block.id).values(checksum='bad-checksum')
            )
            db.commit()
        exported = client.post('/audiobooks/organizer/export-txt', json={'document_id': document_id, 'plan_id': revised['plan_id']})
        self.assertEqual(exported.status_code, 422)
        self.assertEqual(exported.json()['detail']['checksum_mismatch_block_ids'], ['p00001'])

    def test_export_txt_fails_on_invalid_block_ids(self):
        from app.models import BookOrganizationPlan

        client = self._authed_client()
        document_id, plan_id = self._doc_and_plan(client)
        with self.SessionLocal() as db:
            plan = db.query(BookOrganizationPlan).filter(BookOrganizationPlan.id == plan_id).first()
            structure = dict(plan.structure)
            chapters = [dict(ch) for ch in structure['chapters']]
            chapters[0]['block_ids'] = ['p99999']
            structure['chapters'] = chapters
            structure['approved'] = True
            structure['review_status'] = 'approved'
            plan.structure = structure
            db.commit()
        exported = client.post('/audiobooks/organizer/export-txt', json={'document_id': document_id, 'plan_id': plan_id})
        self.assertEqual(exported.status_code, 422)
        self.assertEqual(exported.json()['detail']['invalid_block_ids'], ['p99999'])

    def test_export_before_review_without_canonical_approval_returns_clear_400(self):
        client = self._authed_client()
        document_id, plan_id = self._doc_and_plan(client)

        exported = client.post('/audiobooks/organizer/export-epub', json={'document_id': document_id, 'plan_id': plan_id})

        self.assertEqual(exported.status_code, 400)
        self.assertEqual(exported.json()['detail'], 'Please review and approve book structure before exporting.')

    def test_export_txt_body_matches_preview_body_text(self):
        client = self._authed_client()
        ingest = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Source', 'text': 'Para A\n\nPara B\n\nPara C'})
        document_id = ingest.json()['document']['id']
        plan_id = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id}).json()['plan_id']
        revised = client.post('/audiobooks/organizer/review-structure', json={'document_id': document_id, 'plan_id': plan_id}).json()
        preview = client.post('/audiobooks/organizer/preview', json={'document_id': document_id, 'plan_id': revised['plan_id']}).json()
        exported = client.post('/audiobooks/organizer/export-txt', json={'document_id': document_id, 'plan_id': revised['plan_id']})
        self.assertEqual(exported.status_code, 200)
        preview_parts = []
        for chapter in preview['chapters']:
            preview_parts.append(chapter['chapter_title'])
            preview_parts.extend([paragraph['text'] for paragraph in chapter['paragraphs']])
            preview_parts.append("")
        preview_text = "\n\n".join(preview_parts).rstrip() + "\n"
        self.assertEqual(exported.text, preview_text)

    def test_epub_docx_and_pdf_use_export_metadata(self):
        import zipfile
        from io import BytesIO

        client = self._authed_client()
        ingest = client.post('/audiobooks/organizer/ingest-text', json={'title': 'roughsource', 'text': 'Para A\n\nPara B\n\nPara C'})
        document_id = ingest.json()['document']['id']
        plan_id = client.post('/audiobooks/organizer/propose-plan', json={'document_id': document_id}).json()['plan_id']
        revised = client.post('/audiobooks/organizer/review-structure', json={'document_id': document_id, 'plan_id': plan_id}).json()
        metadata = {
            'document_id': document_id,
            'plan_id': revised['plan_id'],
            'title': 'Who Really Freed the Slaves?',
            'subtitle': 'A Prince of Pan Africa Reader',
            'author': 'Mufasa Study Circle',
            'language': 'en-US',
            'publisher': 'Pan Africa Press',
            'copyright_year': '2026',
        }

        epub = client.post('/audiobooks/organizer/export-epub', json=metadata)
        self.assertEqual(epub.status_code, 200)
        self.assertIn('Who_Really_Freed_the_Slaves.epub', epub.headers['content-disposition'])
        with zipfile.ZipFile(BytesIO(epub.content)) as zf:
            opf = zf.read('OEBPS/content.opf').decode('utf-8')
        self.assertIn('<dc:title>Who Really Freed the Slaves?</dc:title>', opf)
        self.assertIn('<dc:creator>Mufasa Study Circle</dc:creator>', opf)
        self.assertIn('<dc:language>en-US</dc:language>', opf)
        self.assertIn('<dc:publisher>Pan Africa Press</dc:publisher>', opf)
        self.assertIn('<dc:rights>Copyright © 2026 Mufasa Study Circle. All rights reserved.</dc:rights>', opf)
        self.assertNotIn('<dc:creator>Unknown</dc:creator>', opf)

        docx = client.post('/audiobooks/organizer/export-docx', json=metadata)
        self.assertEqual(docx.status_code, 200)
        with zipfile.ZipFile(BytesIO(docx.content)) as zf:
            document_xml = zf.read('word/document.xml').decode('utf-8')
            core_xml = zf.read('docProps/core.xml').decode('utf-8')
        self.assertIn('Who Really Freed the Slaves?', document_xml)
        self.assertIn('by Mufasa Study Circle', document_xml)
        self.assertIn('Copyright © 2026 Mufasa Study Circle. All rights reserved.', document_xml)
        self.assertIn('<dc:title>Who Really Freed the Slaves?</dc:title>', core_xml)
        self.assertIn('<dc:creator>Mufasa Study Circle</dc:creator>', core_xml)
        self.assertIn('<dc:language>en-US</dc:language>', core_xml)

        pdf = client.post('/audiobooks/organizer/export-print-pdf', json=metadata)
        self.assertEqual(pdf.status_code, 200)
        pdf_text = pdf.content.decode('latin-1', errors='ignore')
        self.assertIn('/Title (Who Really Freed the Slaves?)', pdf_text)
        self.assertIn('/Author (Mufasa Study Circle)', pdf_text)
        self.assertIn('/Info', pdf_text)


if __name__ == '__main__':
    unittest.main()
