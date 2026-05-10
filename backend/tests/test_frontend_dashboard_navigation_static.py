import unittest
from pathlib import Path


class DashboardOrganizerNavigationStaticTests(unittest.TestCase):
    def test_global_nav_uses_centralized_helpers_and_logged_out_sign_in_only(self):
        src = Path("src/components/GlobalNav.jsx").read_text()
        self.assertIn('import { getDashboardLabel, isAdminUser } from "../authz";', src)
        self.assertIn('authChecked && user ? (', src)
        self.assertIn('getDashboardLabel(user, rbac)', src)
        self.assertIn('ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer', src)
        self.assertIn('to="/library/organizer"', src)
        self.assertIn('Text Book Organizer', src)
        self.assertIn('Sign In', src)
        self.assertNotIn('VITE_ADMIN_EMAILS', src)
        self.assertNotIn('user.role === "admin"', src)
        logged_out_branch = src.split(') : (', 1)[1]
        self.assertIn('Sign In', logged_out_branch)
        self.assertNotIn('PILOT_NAV_LINKS.map', logged_out_branch)

    def test_authz_helper_admin_and_organizer_rules_are_canonical(self):
        src = Path("src/authz.js").read_text()
        self.assertIn('export function isAdminUser(user, rbac)', src)
        self.assertIn('roles.includes("admin")', src)
        self.assertIn('roles.includes("superadmin")', src)
        self.assertIn('permissions.includes("admin:read_dashboard")', src)
        self.assertIn('userRole === "admin"', src)
        self.assertIn('userRole === "superadmin"', src)
        self.assertIn('user?.is_admin === true', src)
        self.assertNotIn('VITE_ADMIN_EMAILS', src)
        self.assertNotIn('email', src.lower())
        self.assertIn('export function canAccessTextBookOrganizer(user, rbac, featureEnabled, authChecked)', src)
        self.assertIn('featureEnabled &&', src)
        self.assertIn('authChecked &&', src)
        self.assertIn('isAdminUser(user, rbac) || permissions.includes("book_organizer:create_self")', src)
        self.assertIn('export function canAccessMemberDashboard(user, rbac)', src)

    def test_app_imports_helpers_instead_of_defining_scattered_checks(self):
        src = Path("src/App.jsx").read_text()
        self.assertIn('import { canAccessTextBookOrganizer, isAdminUser } from "./authz";', src)
        self.assertNotIn('export function isAdminUser', src)
        self.assertNotIn('VITE_ADMIN_EMAILS', src)
        self.assertIn('return isAdmin ? <AdminOperationsDashboard /> : <MemberDashboard />;', src)
        self.assertIn('canAccessTextBookOrganizer(user, rbac, ENABLE_TEXT_BOOK_ORGANIZER, authChecked)', src)

    def test_text_book_organizer_frontend_flag_defaults_on_for_production_only(self):
        src = Path("src/config.js").read_text()
        self.assertIn('const TEXT_BOOK_ORGANIZER_FLAG = import.meta.env.VITE_ENABLE_TEXT_BOOK_ORGANIZER;', src)
        self.assertIn('TEXT_BOOK_ORGANIZER_FLAG === undefined', src)
        self.assertIn('? !isDev', src)
        self.assertIn('["1", "true", "yes", "on"].includes(normalizedTextBookOrganizerFlag)', src)

    def test_home_and_library_keep_organizer_entry_points_permission_gated_by_props(self):
        home = Path("src/pages/Home.jsx").read_text()
        library = Path("src/pages/LibraryDecolonize.jsx").read_text()
        self.assertIn('Format a Book', home)
        self.assertIn('Upload Book Text', home)
        self.assertIn('authChecked && user', home)
        self.assertIn('ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer', home)
        self.assertNotIn('VITE_ADMIN_EMAILS', home)
        self.assertNotIn('user.role === "admin"', home)
        self.assertIn('Text Book Organizer · Upload Book Text', library)
        self.assertIn('ENABLE_TEXT_BOOK_ORGANIZER && authChecked && canAccessOrganizer', library)
        self.assertNotIn('VITE_ADMIN_EMAILS', library)
        self.assertNotIn('user.role === "admin"', library)


if __name__ == "__main__":
    unittest.main()
