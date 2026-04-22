import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.routes.audiobook import _extract_text_from_pdf


class _StubPage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self):
        return self._text


class _StubReader:
    def __init__(self, pages):
        self.pages = pages


class AudiobookPdfIngestionTests(unittest.TestCase):
    def test_pdf_text_is_extracted_and_normalized(self):
        with patch("app.routes.audiobook.PdfReader", return_value=_StubReader([
            _StubPage("Chapter 1\n\nThis is a valid sample with enough readable content for ingestion."),
            _StubPage("Chapter 2\n\nThis second section preserves downstream segmentation support."),
        ])):
            extracted = _extract_text_from_pdf(b"%PDF-stub")

        self.assertIn("Chapter 1", extracted)
        self.assertIn("Chapter 2", extracted)

    def test_image_only_pdf_fails_clearly(self):
        with patch("app.routes.audiobook.PdfReader", return_value=_StubReader([
            _StubPage(""),
            _StubPage("   "),
        ])):
            with self.assertRaises(HTTPException) as context:
                _extract_text_from_pdf(b"%PDF-image-only")

        self.assertEqual(context.exception.status_code, 422)
        self.assertIn("image-based or unsupported", str(context.exception.detail))

    def test_poor_quality_pdf_fails_clearly(self):
        with patch("app.routes.audiobook.PdfReader", return_value=_StubReader([
            _StubPage("%%%% #### ----"),
        ])):
            with self.assertRaises(HTTPException) as context:
                _extract_text_from_pdf(b"%PDF-bad-encoding")

        self.assertEqual(context.exception.status_code, 422)
        self.assertIn("could not be parsed as text", str(context.exception.detail))


if __name__ == "__main__":
    unittest.main()
