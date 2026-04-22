import os
import tempfile
import unittest
from pathlib import Path


def _build_answers(value: int):
    return [value for _ in range(30)]


class AssessmentDashboardChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_assessment.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        from app.database import Base, SessionLocal, engine
        from app import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_dashboard_returns_saved_latest_and_history(self):
        from app.routes.assessment import (
            AssessmentSubmitRequest,
            get_assessment_dashboard,
            submit_assessment,
        )

        db = self.SessionLocal()
        try:
            first = submit_assessment(
                AssessmentSubmitRequest(
                    userId="family-42",
                    accountId="acct-1",
                    parentId="parent-1",
                    childId="child-9",
                    submissionId="sub-1",
                    responses=_build_answers(4),
                ),
                db,
            )
            second = submit_assessment(
                AssessmentSubmitRequest(
                    userId=first["userId"],
                    accountId="acct-1",
                    parentId="parent-1",
                    childId="child-9",
                    submissionId="sub-2",
                    responses=_build_answers(5),
                ),
                db,
            )

            dashboard = get_assessment_dashboard(second["userId"], db)
            self.assertTrue(dashboard["saved"])
            self.assertEqual(dashboard["latest"]["submissionId"], "sub-2")
            self.assertEqual(dashboard["latest"]["childId"], "child-9")
            self.assertGreaterEqual(len(dashboard["history"]), 2)
        finally:
            db.close()

    def test_no_false_success_when_result_missing(self):
        from fastapi import HTTPException

        from app.routes.assessment import get_assessment_dashboard

        db = self.SessionLocal()
        try:
            with self.assertRaises(HTTPException) as context:
                get_assessment_dashboard("99999", db)
            self.assertEqual(context.exception.status_code, 404)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
