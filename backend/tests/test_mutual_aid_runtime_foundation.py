import importlib
import os
import tempfile
import unittest
from pathlib import Path


EXPECTED_MUTUAL_AID_TABLES = {
    "mutual_aid_funds",
    "mutual_aid_contributions",
    "mutual_aid_requests",
    "mutual_aid_request_documents",
    "mutual_aid_reviews",
    "mutual_aid_decisions",
    "mutual_aid_disbursements",
    "mutual_aid_policy_versions",
    "mutual_aid_member_acceptances",
    "mutual_aid_audit_logs",
    "mutual_aid_request_status_history",
    "mutual_aid_committee_members",
    "mutual_aid_conflict_disclosures",
    "mutual_aid_appeals",
    "mutual_aid_fraud_reviews",
    "mutual_aid_reconciliation_reports",
    "mutual_aid_category_budgets",
    "mutual_aid_vendor_recipients",
}


class MutualAidRuntimeFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import sqlalchemy  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("SQLAlchemy is required for Mutual Aid foundation tests") from exc

        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_mutual_aid_foundation.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION"] = "true"
        os.environ["ENABLE_MUTUAL_AID_REQUEST_INTAKE"] = "false"
        os.environ["ENABLE_MUTUAL_AID_REVIEW_WORKFLOW"] = "false"
        os.environ["ENABLE_MUTUAL_AID_PAYMENTS"] = "false"

        import app.config as config_module
        import app.database as database_module

        importlib.reload(config_module)
        importlib.reload(database_module)
        from app import models  # noqa: F401

        database_module.init_db()
        cls.database_module = database_module
        cls.SessionLocal = database_module.SessionLocal

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp_dir"):
            cls.temp_dir.cleanup()

    def test_mutual_aid_tables_are_created(self):
        from sqlalchemy import inspect

        inspector = inspect(self.database_module.engine)
        table_names = set(inspector.get_table_names())
        self.assertTrue(EXPECTED_MUTUAL_AID_TABLES.issubset(table_names))

    def test_default_fund_can_be_read_with_activation_threshold(self):
        from app.models import MutualAidFund
        from app.services.mutual_aid import DEFAULT_MUTUAL_AID_FUND_NAME

        db = self.SessionLocal()
        try:
            fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one()
            self.assertEqual(fund.status, "Building Toward Activation")
            self.assertEqual(fund.activation_threshold, 20000)
            self.assertEqual(fund.current_balance, 0)
            self.assertEqual(fund.available_balance, 0)
            self.assertEqual(fund.reserved_balance, 0)
            self.assertEqual(fund.currency, "USD")
        finally:
            db.close()

    def test_runtime_safety_feature_flags_are_closed(self):
        from app.services.mutual_aid import mutual_aid_feature_flags

        flags = mutual_aid_feature_flags()
        self.assertTrue(flags["ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION"])
        self.assertFalse(flags["ENABLE_MUTUAL_AID_REQUEST_INTAKE"])
        self.assertFalse(flags["ENABLE_MUTUAL_AID_REVIEW_WORKFLOW"])
        self.assertFalse(flags["ENABLE_MUTUAL_AID_PAYMENTS"])

    def test_no_payout_payment_request_intake_or_wallet_routes_exist(self):
        from app.main import app

        route_paths = {route.path.lower() for route in app.routes}
        forbidden_terms = ("mutual-aid/payout", "mutual-aid/payment", "mutual-aid/request", "wallet", "cash-balance")
        for path in route_paths:
            self.assertFalse(any(term in path for term in forbidden_terms), path)

    def test_no_wallet_or_cash_balance_models_exist(self):
        from app.database import Base

        table_names = set(Base.metadata.tables)
        self.assertNotIn("wallets", table_names)
        self.assertNotIn("cash_balances", table_names)
        self.assertNotIn("mutual_aid_wallets", table_names)
        self.assertNotIn("mutual_aid_cash_balances", table_names)


class MutualAidMigrationFileTests(unittest.TestCase):
    def test_migration_file_lists_all_foundation_tables(self):
        migration = Path("backend/migrations/20260626_mutual_aid_runtime_foundation.sql")
        contents = migration.read_text()
        for table_name in EXPECTED_MUTUAL_AID_TABLES:
            self.assertIn(table_name, contents)
        self.assertIn("Building Toward Activation", contents)
        self.assertIn("20000", contents)


if __name__ == "__main__":
    unittest.main()
