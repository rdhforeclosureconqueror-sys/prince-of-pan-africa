import os
import unittest
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


if __name__ == '__main__':
    unittest.main()
