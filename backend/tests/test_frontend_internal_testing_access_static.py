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


def test_global_nav_uses_internal_society_builder_access_and_scrollable_mobile_menu():
    nav = Path("src/components/GlobalNav.jsx").read_text()
    css = Path("src/styles/globalNav.css").read_text()
    assert "canAccessSocietyBuilder(user, rbac, SOCIETY_BUILDER_ENABLED, authChecked)" in nav
    assert "{canViewSocietyBuilder ? (" in nav
    assert 'to="/simba-main-hub"' in nav
    assert 'to="/societies"' in nav
    assert 'to="/societies/start"' in nav
    assert 'to="/societies/register-chapter"' in nav
    assert 'to="/admin/societies/chapters"' in nav
    assert '{isAdmin ? <Link to="/admin/societies/chapters"' in nav
    assert "max-height: calc(100dvh - 86px - env(safe-area-inset-bottom, 0px));" in css
    assert "overflow-y: auto;" in css
    assert "-webkit-overflow-scrolling: touch;" in css
    assert "padding-bottom: calc(18px + env(safe-area-inset-bottom, 0px));" in css


def test_global_nav_keeps_mutual_aid_admin_links_visible_for_admin_override():
    nav = Path("src/components/GlobalNav.jsx").read_text()
    assert 'to="/admin/mutual-aid/executive"' in nav
    assert 'to="/admin/mutual-aid/dashboard"' in nav
    assert 'to="/admin/mutual-aid/governance"' in nav
    assert 'to="/admin/mutual-aid/allowlist-preview"' in nav
    assert 'to="/admin/mutual-aid/review-preview"' in nav
    assert "{isAdmin ? (" in nav
