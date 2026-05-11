import os
import io
import unittest
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient


CHAPTER_TITLES = [
    "WHO REALLY FREED THE SLAVES?",
    "WHEN DID THE WAR BECOME BLACK?",
    "THE PRICE OF SLAVERY",
    "WHEN FREEDOM CHANGED MEANING",
    "THE UNION NEEDED SAVING FROM WHAT?",
    "THE WAR INSIDE THE WAR",
    "FORTY ACRES… THEN WHAT?",
    "WHEN THE DEAL CHANGED",
    "FREEDOM WITHOUT POWER",
    "WHEN WE BUILT OUR OWN WORLD",
    "WHEN THEY REDREW THE MAP",
    "WHEN CIVIL RIGHTS REPLACED LIBERATION",
    "DID THE SYSTEM EVER REALLY CHANGE?",
    "DID AMERICA EVER RECOVER FROM SLAVERY?",
    "WHOSE LAND? WHOSE FREEDOM?",
    "THE MEMORY WAR",
    "WHO OWNS THE FUTURE?",
]
CHAPTER_MARKERS = [
    "CHAPTER ONE", "CHAPTER TWO", "CHAPTER THREE", "CHAPTER FOUR", "CHAPTER FIVE", "CHAPTER SIX",
    "CHAPTER SEVEN", "CHAPTER EIGHT", "CHAPTER NINE", "CHAPTER TEN", "CHAPTER ELEVEN",
    "CHAPTER TWELVE", "CHAPTER THIRTEEN", "CHAPTER FOURTEEN", "CHAPTER FIFTEEN",
    "CHAPTER SIXTEEN", "CHAPTER SEVENTEEN",
]


def build_manuscript(words_per_chapter: int = 25) -> str:
    parts = []
    filler = " ".join(f"word{i}" for i in range(words_per_chapter))
    for marker, title in zip(CHAPTER_MARKERS, CHAPTER_TITLES):
        parts.append(f"{marker}\n{title}\n\nOpening\n{filler}\n\n⸻\n\nClosing\n{filler}")
    parts.append("EPILOGUE\nTHE QUESTION THAT REMAINS\n\nOpening\n" + filler)
    return "\n\n".join(parts)


class ExplicitChapterDetectionUnitTests(unittest.TestCase):
    def test_detects_explicit_word_chapters(self):
        from app.routes.audiobook import _detect_book_organizer_explicit_chapters

        chapters = _detect_book_organizer_explicit_chapters("CHAPTER ONE\nFIRST TITLE\n\nOpening\nBody.\n\nCHAPTER TWO\nSECOND TITLE\n\nClosing\nBody.")
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0]["marker"], "CHAPTER ONE")
        self.assertEqual(chapters[0]["title"], "FIRST TITLE")

    def test_detects_epilogue(self):
        from app.routes.audiobook import _detect_book_organizer_explicit_chapters

        chapters = _detect_book_organizer_explicit_chapters("CHAPTER 1\nA Beginning\n\nBody\n\nEPILOGUE\nThe End\n\nBody")

        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[1]["marker"], "EPILOGUE")
        self.assertEqual(chapters[1]["type"], "epilogue")
        self.assertEqual(chapters[1]["title"], "The End")

    def test_does_not_split_on_opening_closing(self):
        from app.routes.audiobook import _detect_book_organizer_explicit_chapters

        chapters = _detect_book_organizer_explicit_chapters("CHAPTER I\nRoman Start\n\nOpening\nBody\n\nClosing\nBody\n\nCHAPTER II\nNext\n\nOpening\nBody")

        self.assertEqual(len(chapters), 2)
        self.assertIn("Opening", [section["title"] for section in chapters[0]["sections"]])
        self.assertIn("Closing", [section["title"] for section in chapters[0]["sections"]])

    def test_does_not_split_on_divider_marks(self):
        from app.routes.audiobook import _detect_book_organizer_explicit_chapters

        chapters = _detect_book_organizer_explicit_chapters("CHAPTER 1\nOne\n\nBody\n\n⸻\n\nBody\n\nCHAPTER 2\nTwo\n\nBody")

        self.assertEqual(len(chapters), 2)
        self.assertIn("⸻", chapters[0]["body"])


    def test_does_not_split_on_bullet_lists(self):
        from app.routes.audiobook import _detect_book_organizer_explicit_chapters

        chapters = _detect_book_organizer_explicit_chapters(
            "CHAPTER 1\nOne\n\n- Bullet one\n- Bullet two\n\nCHAPTER 2\nTwo\n\n• Bullet three"
        )

        self.assertEqual(len(chapters), 2)
        self.assertIn("- Bullet one", chapters[0]["body"])

    def test_does_not_create_part_chapters_in_explicit_book_structure(self):
        from app.routes.audiobook import _detect_book_organizer_explicit_chapters

        long_body = " ".join(["longchapter"] * 1200)
        chapters = _detect_book_organizer_explicit_chapters(f"CHAPTER 1\nLong One\n\n{long_body}\n\nCHAPTER 2\nLong Two\n\n{long_body}")

        self.assertEqual(len(chapters), 2)
        self.assertNotIn("Part", chapters[0]["chapter_title"])

    def test_short_emphasis_lines_and_attributions_are_not_section_headings(self):
        from app.routes.audiobook import _book_organizer_extract_sections

        body = "Opening\nWhy?\n\nFast.\n\n— Frederick Douglass\n\nThe Story Most People Inherit\nActual section body."

        sections = _book_organizer_extract_sections(body)

        self.assertEqual([section["title"] for section in sections], ["Opening", "The Story Most People Inherit"])
        self.assertIn("Why?", sections[0]["body"])
        self.assertIn("Fast.", sections[0]["body"])
        self.assertIn("— Frederick Douglass", sections[0]["body"])

    def test_over_splitting_warning_when_chapter_count_exceeds_threshold(self):
        from app.routes.audiobook import _book_organizer_structure_warnings

        warnings = _book_organizer_structure_warnings(81)

        self.assertEqual(warnings[0]["message"], "Possible over-splitting detected")


class ExplicitChapterOrganizerApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_book_organizer_explicit_chapters.db')
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
        from app.authz import seed_rbac_defaults

        settings.ENABLE_TEXT_BOOK_ORGANIZER = True
        with self.SessionLocal() as db:
            db.query(BookOrganizationPlan).delete()
            db.query(BookOrganizerBlock).delete()
            db.query(BookOrganizerDocument).delete()
            db.query(UserRole).delete()
            db.query(User).delete()
            db.commit()
            db.add(User(email='explicit@example.com', password_hash=hash_password('password123'), role='subscriber'))
            db.commit()
            seed_rbac_defaults(db)

    def _authed_client(self):
        res = self.client.post('/auth/login', json={'email': 'explicit@example.com', 'password': 'password123'})
        self.assertEqual(res.status_code, 200)
        client = TestClient(self.client.app)
        client.cookies.set('mufasa_session', res.cookies.get('mufasa_session'))
        return client

    def test_does_not_create_paragraph_chapters_when_explicit_chapters_exist(self):
        client = self._authed_client()
        text = "CHAPTER ONE\nACTUAL ONE\n\nOpening\nPara A\n\nClosing\nPara B\n\nCHAPTER TWO\nACTUAL TWO\n\nOpening\nPara C"
        doc = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Explicit', 'text': text}).json()['document']['id']

        plan = client.post('/audiobooks/organizer/propose-plan', json={'document_id': doc}).json()['structure']

        self.assertEqual(plan['detection_mode'], 'explicit_chapter_markers')
        self.assertEqual(plan['chapter_count'], 2)
        self.assertEqual([chapter['title'] for chapter in plan['chapters']], ['ACTUAL ONE', 'ACTUAL TWO'])

    def test_large_manuscript_expected_17_chapters_plus_epilogue(self):
        client = self._authed_client()
        doc = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Large', 'text': build_manuscript()}).json()['document']['id']
        plan_res = client.post('/audiobooks/organizer/propose-plan', json={'document_id': doc})
        self.assertEqual(plan_res.status_code, 200)
        structure = plan_res.json()['structure']

        self.assertEqual(structure['chapter_count'], 18)
        self.assertEqual(structure['chapters'][0]['chapter_title'], 'Chapter One: Who Really Freed the Slaves?')
        self.assertEqual(structure['chapters'][-1]['chapter_title'], 'Epilogue: The Question That Remains')
        self.assertEqual(structure['chapters'][-1]['type'], 'epilogue')

        preview = client.post('/audiobooks/organizer/preview', json={'document_id': doc, 'plan_id': plan_res.json()['plan_id']})
        self.assertEqual(preview.status_code, 200)
        preview_body = preview.json()
        self.assertEqual(preview_body['detected_chapter_count'], 18)
        self.assertEqual(len(preview_body['chapter_titles']), 18)
        self.assertIn('word_count', preview_body['chapters'][0])

        approved = client.post('/audiobooks/organizer/review-structure', json={'document_id': doc, 'plan_id': plan_res.json()['plan_id']})
        self.assertEqual(approved.status_code, 200)
        epub = client.post('/audiobooks/organizer/export-epub', json={'document_id': doc, 'plan_id': approved.json()['plan_id'], 'title': 'Large', 'author': 'Author Name', 'language': 'en'})
        self.assertEqual(epub.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(epub.content)) as zf:
            content_files = [name for name in zf.namelist() if name.startswith('OEBPS/chapter-') and name.endswith('.xhtml')]
            nav = zf.read('OEBPS/nav.xhtml').decode('utf-8')
            ncx = zf.read('OEBPS/toc.ncx').decode('utf-8')
            chapter_one = zf.read('OEBPS/chapter-1.xhtml').decode('utf-8')
            chapter_seventeen = zf.read('OEBPS/chapter-17.xhtml').decode('utf-8')
            epilogue = zf.read('OEBPS/chapter-18.xhtml').decode('utf-8')

            self.assertEqual(len(content_files), 18)
            self.assertEqual(nav.count('<li><a href='), 18)
            self.assertEqual(ncx.count('<navPoint '), 18)
            self.assertIn('Chapter One: Who Really Freed the Slaves?', nav)
            self.assertIn('Chapter Seventeen: Who Owns the Future?', nav)
            self.assertIn('Epilogue: The Question That Remains', nav)
            self.assertIn('<h1>Chapter One: Who Really Freed the Slaves?</h1><h2>Opening</h2>', chapter_one)
            self.assertEqual(chapter_one.count('<h1>Chapter One: Who Really Freed the Slaves?</h1>'), 1)
            self.assertIn('<h1>Chapter Seventeen: Who Owns the Future?</h1>', chapter_seventeen)
            self.assertIn('<h1>Epilogue: The Question That Remains</h1>', epilogue)

    def test_txt_export_uses_canonical_headings_without_duplicate_raw_marker_or_title(self):
        client = self._authed_client()
        text = 'CHAPTER ONE\nWHO REALLY FREED THE SLAVES?\n\nOpening\n“If I could save the Union without freeing any slave, I would do it.”\n\nCHAPTER TWO\nNEXT TITLE\n\nOpening\nBody'
        doc = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Explicit', 'text': text}).json()['document']['id']
        plan = client.post('/audiobooks/organizer/propose-plan', json={'document_id': doc}).json()['plan_id']
        approved = client.post('/audiobooks/organizer/review-structure', json={'document_id': doc, 'plan_id': plan}).json()['plan_id']

        export = client.post('/audiobooks/organizer/export-txt', json={'document_id': doc, 'plan_id': approved})

        self.assertEqual(export.status_code, 200)
        body = export.text
        self.assertIn('Chapter One: Who Really Freed the Slaves?\n\nOpening\n\n“If I could save the Union without freeing any slave, I would do it.”', body)
        self.assertEqual(body.count('Chapter One: Who Really Freed the Slaves?'), 1)
        self.assertNotIn('CHAPTER ONE\n\nWHO REALLY FREED THE SLAVES?', body)

    def test_publishing_exports_are_generated_from_canonical_structure(self):
        client = self._authed_client()
        text = 'CHAPTER ONE\nWHO REALLY FREED THE SLAVES?\n\nOpening\nWhy?\n\nFast.\n\n— Frederick Douglass\n\nBody one\n\n- Bullet one\n- Bullet two\n\nCHAPTER TWO\nNEXT TITLE\n\nClosing\nBody two'
        doc = client.post('/audiobooks/organizer/ingest-text', json={'title': 'Publishable', 'text': text}).json()['document']['id']
        plan = client.post('/audiobooks/organizer/propose-plan', json={'document_id': doc}).json()['plan_id']
        approved = client.post('/audiobooks/organizer/review-structure', json={'document_id': doc, 'plan_id': plan}).json()['plan_id']
        payload = {'document_id': doc, 'plan_id': approved, 'title': 'Publishable', 'author': 'Author Name', 'language': 'en'}

        docx = client.post('/audiobooks/organizer/export-docx', json=payload)
        epub = client.post('/audiobooks/organizer/export-epub', json=payload)
        pdf = client.post('/audiobooks/organizer/export-print-pdf', json=payload)

        self.assertEqual(docx.status_code, 200)
        self.assertEqual(epub.status_code, 200)
        self.assertEqual(epub.headers['content-type'].split(';')[0], 'application/epub+zip')
        self.assertIn('attachment;', epub.headers['content-disposition'])
        self.assertIn('Publishable.epub', epub.headers['content-disposition'])
        self.assertTrue(epub.headers['content-disposition'].strip().endswith('.epub"'))
        self.assertEqual(pdf.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(docx.content)) as zf:
            document_xml = zf.read('word/document.xml').decode('utf-8')
            self.assertIn('Table of Contents', document_xml)
            self.assertIn('Chapter One: Who Really Freed the Slaves?', document_xml)
            self.assertNotIn('CHAPTER ONE', document_xml)
        with zipfile.ZipFile(io.BytesIO(epub.content)) as zf:
            self.assertEqual(zf.read('mimetype'), b'application/epub+zip')
            opf = zf.read('OEBPS/content.opf').decode('utf-8')
            nav = zf.read('OEBPS/nav.xhtml').decode('utf-8')
            ncx = zf.read('OEBPS/toc.ncx').decode('utf-8')
            chapter = zf.read('OEBPS/chapter-1.xhtml').decode('utf-8')
            self.assertIn('<dc:title>Publishable</dc:title>', opf)
            self.assertIn('toc="ncx"', opf)
            self.assertIn('OEBPS/toc.ncx', '\n'.join(zf.namelist()))
            self.assertIn('chapter-1.xhtml', nav)
            self.assertEqual(nav.count('<li><a href='), 2)
            self.assertNotIn('Opening', nav)
            self.assertNotIn('Closing', nav)
            self.assertIn('navPoint-1', ncx)
            self.assertEqual(chapter.count('<h1>Chapter One: Who Really Freed the Slaves?</h1>'), 1)
            self.assertNotIn('<h2>Why?</h2>', chapter)
            self.assertNotIn('<h2>Fast.</h2>', chapter)
            self.assertNotIn('<h2>— Frederick Douglass</h2>', chapter)
            self.assertIn('<p>Why?</p>', chapter)
            self.assertIn('<p>Fast.</p>', chapter)
            self.assertIn('<ul><li>Bullet one</li><li>Bullet two</li></ul>', chapter)
            self.assertNotIn('CHAPTER ONE', chapter)
        self.assertTrue(pdf.content.startswith(b'%PDF-1.4'))
        self.assertIn(b'/MediaBox [0 0 432 648]', pdf.content)


if __name__ == '__main__':
    unittest.main()
