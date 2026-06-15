import os
import tempfile
import unittest
from pathlib import Path


class BillingHelperSafetyTests(unittest.TestCase):
    def test_tier_and_role_mapping_helpers_fail_closed(self):
        from app.services.billing import (
            normalize_subscription_plan,
            role_for_subscription_tier,
            tier_for_subscription_plan,
        )

        self.assertEqual(normalize_subscription_plan("community"), "community")
        self.assertEqual(normalize_subscription_plan("builder"), "builder")
        self.assertEqual(tier_for_subscription_plan("community"), "community_member")
        self.assertEqual(tier_for_subscription_plan("builder"), "builder_member")
        self.assertEqual(role_for_subscription_tier("community_member"), "community_member")
        self.assertEqual(role_for_subscription_tier("builder_member"), "builder_member")

        self.assertIsNone(normalize_subscription_plan("subscriber"))
        self.assertIsNone(tier_for_subscription_plan("subscriber"))
        self.assertIsNone(role_for_subscription_tier("subscriber"))
        self.assertIsNone(role_for_subscription_tier("admin"))

    def test_unknown_or_unconfigured_price_ids_fail_closed(self):
        from app.services.billing import tier_for_price_id

        old_values = {key: os.environ.get(key) for key in ["STRIPE_COMMUNITY_PRICE_ID", "STRIPE_BUILDER_PRICE_ID"]}
        try:
            os.environ["STRIPE_COMMUNITY_PRICE_ID"] = "price_community_test"
            os.environ["STRIPE_BUILDER_PRICE_ID"] = "price_builder_test"

            self.assertEqual(tier_for_price_id("price_community_test"), "community_member")
            self.assertEqual(tier_for_price_id("price_builder_test"), "builder_member")
            self.assertIsNone(tier_for_price_id("price_unknown"))
            self.assertIsNone(tier_for_price_id(""))
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_stripe_checkout_requires_explicit_safe_config(self):
        from app.services.billing import stripe_checkout_enabled, stripe_is_configured

        old_values = {key: os.environ.get(key) for key in ["STRIPE_SECRET_KEY", "ENABLE_STRIPE_CHECKOUT"]}
        try:
            os.environ.pop("STRIPE_SECRET_KEY", None)
            os.environ["ENABLE_STRIPE_CHECKOUT"] = "true"
            self.assertFalse(stripe_is_configured())
            self.assertFalse(stripe_checkout_enabled())
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class BillingSubscriptionModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import sqlalchemy  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("SQLAlchemy is required for subscription model tests") from exc

        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_billing.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine

        Base.metadata.create_all(bind=engine)
        cls.SessionLocal = SessionLocal

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp_dir"):
            cls.temp_dir.cleanup()

    def test_subscription_model_defaults_without_stripe_credentials(self):
        from app.models import Subscription, User

        db = self.SessionLocal()
        try:
            user = User(email="billing-model@example.com", password_hash="x", role="member")
            db.add(user)
            db.commit()
            subscription = Subscription(user_id=user.id)
            db.add(subscription)
            db.commit()
            db.refresh(subscription)

            self.assertEqual(subscription.tier, "community_member")
            self.assertEqual(subscription.status, "pending")
            self.assertEqual(subscription.raw_metadata, {})
            self.assertEqual(subscription.user.email, "billing-model@example.com")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
