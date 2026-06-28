from pathlib import Path


def test_frontend_has_admin_internal_society_builder_override():
    authz = Path("src/authz.js").read_text()
    app = Path("src/App.jsx").read_text()
    assert "export function canUseInternalTestingAccess(user, rbac)" in authz
    assert "featureEnabled || canUseInternalTestingAccess(user, rbac)" in authz
    assert "canAccessSocietyBuilder(user, rbac, SOCIETY_BUILDER_ENABLED, authChecked)" in app
    assert "<AdminSocietyBuilderRoute authChecked={authChecked} user={user} rbac={rbac} isAdmin={isAdmin}>" in app


def test_frontend_mutual_aid_admin_routes_are_registered_for_admin_override():
    app = Path("src/App.jsx").read_text()
    assert "isAdmin || ENABLE_MUTUAL_AID_OPERATIONS_DASHBOARD || ENABLE_MUTUAL_AID_OBSERVABILITY" in app
    assert "isAdmin || ENABLE_MUTUAL_AID_GOVERNANCE_CENTER" in app
    assert "isAdmin || ENABLE_MUTUAL_AID_EXECUTIVE_DASHBOARD" in app
    assert "!ENABLE_MUTUAL_AID_REVIEW_WORKFLOW && !isAdmin" in app
    assert "!ENABLE_MUTUAL_AID_FINANCIAL_CONTROLS && !isAdmin" in app
