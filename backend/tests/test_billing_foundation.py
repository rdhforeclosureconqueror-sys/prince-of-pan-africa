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

class BillingPhase3SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import sqlalchemy  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("SQLAlchemy is required for billing phase 3 tests") from exc

        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.temp_dir.name) / "test_billing_phase3.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["STRIPE_COMMUNITY_PRICE_ID"] = "price_1TiUAM3JOrXsFGB5q4mSofyD"
        os.environ["STRIPE_BUILDER_PRICE_ID"] = "price_1TiUBJ3JOrXsFGB5OPAPcnl4"

        from app import models  # noqa: F401
        from app.database import Base, SessionLocal, engine
        from app.authz import seed_rbac_defaults

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_rbac_defaults(db)
        finally:
            db.close()
        cls.SessionLocal = SessionLocal

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp_dir"):
            cls.temp_dir.cleanup()

    def test_only_active_known_price_grants_builder_role(self):
        from app.authz import get_user_role_names
        from app.models import Subscription, User
        from app.services.billing import sync_paid_roles_for_user

        db = self.SessionLocal()
        try:
            user = User(email="phase3-builder@example.com", password_hash="x", role="member")
            db.add(user)
            db.commit()
            db.refresh(user)

            db.add(
                Subscription(
                    user_id=user.id,
                    stripe_customer_id="cus_builder",
                    stripe_subscription_id="sub_builder_active",
                    stripe_price_id="price_1TiUBJ3JOrXsFGB5OPAPcnl4",
                    tier="builder_member",
                    status="active",
                )
            )
            db.flush()
            sync_paid_roles_for_user(db, user)
            db.commit()

            roles = get_user_role_names(db, user)
            self.assertIn("builder_member", roles)
            self.assertEqual(user.role, "builder_member")
        finally:
            db.close()

    def test_past_due_unpaid_incomplete_canceled_and_unknown_do_not_grant_paid_access(self):
        from app.authz import get_user_role_names
        from app.models import Subscription, User
        from app.services.billing import sync_paid_roles_for_user

        disallowed = ["past_due", "unpaid", "incomplete", "canceled", "unknown"]
        db = self.SessionLocal()
        try:
            for status_name in disallowed:
                user = User(email=f"phase3-{status_name}@example.com", password_hash="x", role="member")
                db.add(user)
                db.flush()
                db.add(
                    Subscription(
                        user_id=user.id,
                        stripe_customer_id=f"cus_{status_name}",
                        stripe_subscription_id=f"sub_{status_name}",
                        stripe_price_id="price_1TiUAM3JOrXsFGB5q4mSofyD",
                        tier="community_member",
                        status=status_name,
                    )
                )
                db.flush()
                sync_paid_roles_for_user(db, user)
                roles = get_user_role_names(db, user)
                self.assertNotIn("builder_member", roles)
                self.assertEqual(user.role, "member")
            db.rollback()
        finally:
            db.close()

    def test_upsert_subscription_rejects_unknown_price_id(self):
        from app.services.billing import upsert_subscription_from_stripe

        db = self.SessionLocal()
        try:
            with self.assertRaises(ValueError):
                upsert_subscription_from_stripe(
                    db,
                    {
                        "id": "sub_unknown_price",
                        "customer": "cus_unknown",
                        "status": "active",
                        "items": {"data": [{"price": {"id": "price_not_approved"}}]},
                        "metadata": {},
                    },
                )
        finally:
            db.close()
