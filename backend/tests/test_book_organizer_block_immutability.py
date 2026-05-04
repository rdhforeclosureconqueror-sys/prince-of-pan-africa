import os
import unittest
from pathlib import Path


class BookOrganizerBlockImmutabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path('/tmp/test_book_organizer_block_immutability.db')
        if db_path.exists():
            db_path.unlink()

        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        os.environ['SESSION_SECRET'] = 'test-session-secret'
        os.environ['ENVIRONMENT'] = 'test'

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal

    def setUp(self):
        from app.models import BookOrganizationPlan, BookOrganizerBlock, BookOrganizerDocument, User
        from app.security import hash_password

        with self.SessionLocal() as db:
            db.query(BookOrganizationPlan).delete()
            db.query(BookOrganizerBlock).delete()
            db.query(BookOrganizerDocument).delete()
            db.query(User).delete()
            db.commit()

            user = User(email='organizer-owner@example.com', password_hash=hash_password('password123'), role='member')
            db.add(user)
            db.commit()
            self.user_id = user.id

    def test_checksum_is_derived_from_original_block_text(self):
        from app.models import BookOrganizerBlock, BookOrganizerDocument, compute_text_checksum

        original_text = 'Paragraph one.\n\nParagraph two.'

        with self.SessionLocal() as db:
            doc = BookOrganizerDocument(
                user_id=self.user_id,
                title='Immutable Manuscript',
                source_text_hash=compute_text_checksum(original_text),
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            block = BookOrganizerBlock(
                document_id=doc.id,
                block_index=1,
                block_id='blk_0001',
                text=original_text,
                checksum='incorrect-value-should-be-overwritten',
            )
            db.add(block)
            db.commit()
            db.refresh(block)

            self.assertEqual(block.checksum, compute_text_checksum(original_text))

    def test_block_text_and_checksum_are_immutable_after_creation(self):
        from app.models import BookOrganizerBlock, BookOrganizerDocument, compute_text_checksum

        original_text = 'Original paragraph remains unchanged.'

        with self.SessionLocal() as db:
            doc = BookOrganizerDocument(
                user_id=self.user_id,
                title='Immutable Guardrail',
                source_text_hash=compute_text_checksum(original_text),
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            block = BookOrganizerBlock(
                document_id=doc.id,
                block_index=1,
                block_id='blk_guardrail_1',
                text=original_text,
                checksum=compute_text_checksum(original_text),
            )
            db.add(block)
            db.commit()
            db.refresh(block)

            block.text = 'Mutated text should fail.'
            with self.assertRaises(ValueError):
                db.commit()
            db.rollback()

            reloaded = db.query(BookOrganizerBlock).filter(BookOrganizerBlock.id == block.id).first()
            self.assertEqual(reloaded.text, original_text)
            self.assertEqual(reloaded.checksum, compute_text_checksum(original_text))


if __name__ == '__main__':
    unittest.main()
