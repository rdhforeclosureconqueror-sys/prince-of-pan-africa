import importlib
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from tests.session_test_utils import session_cookie

ADMIN_EMAIL = "rdhforeclosureconqueror@gmail.com"


def build_app(society_enabled="false", mutual_review_enabled="true"):
    tmp = tempfile.TemporaryDirectory()
    os.environ["DATABASE_URL"] = f"sqlite:///{Path(tmp.name) / 'admin-internal.db'}"
    os.environ["APP_ENV"] = "test"
    os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"
    os.environ["SESSION_SECRET"] = "test-session-secret"
    os.environ["SOCIETY_BUILDER_ENABLED"] = society_enabled
    os.environ["MUTUAL_AID_REQUESTS_ENABLED"] = "true"
    os.environ["MUTUAL_AID_REVIEW_ENABLED"] = mutual_review_enabled
    os.environ["ENABLE_MUTUAL_AID_PAYMENTS"] = "false"

    import app.config as config
    import app.database as database
    import app.models as models
    import app.authz as authz
    import app.routes.society_builder as society_builder_route
    import app.routes.mutual_aid as mutual_aid_route
    import app.main as main

    for module in (config, database, models, authz, society_builder_route, mutual_aid_route, main):
        importlib.reload(module)
    database.init_db()
    return tmp, database, models, authz, TestClient(main.app)


def seed_user(database, models, authz, email, role="community_member"):
    db = database.SessionLocal()
    try:
        user = models.User(email=email, password_hash="x", role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        authz.seed_rbac_defaults(db)
        return user.id
    finally:
        db.close()


def test_seed_rbac_upgrades_existing_testing_email_to_superadmin_idempotently():
    tmp, database, models, authz, _ = build_app()
    try:
        user_id = seed_user(database, models, authz, ADMIN_EMAIL.upper(), "community_member")
        db = database.SessionLocal()
        try:
            from app.services.admin_seed import seed_admin

            first = seed_admin()
            authz.seed_rbac_defaults(db)
            second = seed_admin()
            authz.seed_rbac_defaults(db)
            user = db.query(models.User).filter(models.User.id == user_id).one()
            role_names = authz.get_user_role_names(db, user)
            assert first["skipped"] is False
            assert second["skipped"] is False
            assert user.email == ADMIN_EMAIL
            assert user.role == "superadmin"
            assert "superadmin" in role_names
            assert db.query(models.User).filter(models.User.email == ADMIN_EMAIL).count() == 1
        finally:
            db.close()
    finally:
        tmp.cleanup()


def test_testing_admin_can_access_society_builder_when_feature_flag_is_off():
    tmp, database, models, authz, client = build_app(society_enabled="false")
    try:
        admin_id = seed_user(database, models, authz, ADMIN_EMAIL, "superadmin")
        member_id = seed_user(database, models, authz, "normal@example.com", "community_member")

        admin_hub = client.get("/society-builder/main-hub", cookies=session_cookie(admin_id))
        member_hub = client.get("/society-builder/main-hub", cookies=session_cookie(member_id))
        public_hub = client.get("/society-builder/main-hub")
        admin_chapters = client.get("/society-builder/admin/chapter-applications", cookies=session_cookie(admin_id))
        member_chapters = client.get("/society-builder/admin/chapter-applications", cookies=session_cookie(member_id))

        assert admin_hub.status_code == 200, admin_hub.text
        assert admin_chapters.status_code == 200, admin_chapters.text
        assert member_hub.status_code == 404
        assert public_hub.status_code == 404
        assert member_chapters.status_code in {403, 404}
    finally:
        tmp.cleanup()


def test_testing_admin_can_access_mutual_aid_admin_routes_and_member_cannot():
    tmp, database, models, authz, client = build_app(mutual_review_enabled="true")
    try:
        admin_id = seed_user(database, models, authz, ADMIN_EMAIL, "superadmin")
        member_id = seed_user(database, models, authz, "normal-mutual@example.com", "community_member")

        admin_response = client.get("/mutual-aid/admin/requests", cookies=session_cookie(admin_id))
        member_response = client.get("/mutual-aid/admin/requests", cookies=session_cookie(member_id))

        assert admin_response.status_code == 200, admin_response.text
        assert member_response.status_code == 403
    finally:
        tmp.cleanup()
