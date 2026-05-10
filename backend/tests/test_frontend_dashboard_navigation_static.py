import unittest
from pathlib import Path


class DashboardOrganizerNavigationStaticTests(unittest.TestCase):
    def test_global_nav_hides_dashboard_until_authenticated_and_gates_organizer_by_access_state(self):
        src = Path("src/components/GlobalNav.jsx").read_text()
        self.assertIn('if (link.to === "/dashboard" && (!authChecked || !user)) return null;', src)
        self.assertIn('isAdmin ? "Operations Deck" : "Member Dashboard"', src)
        self.assertIn('ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer', src)
        self.assertIn('to="/library/organizer"', src)
        self.assertIn('Text Book Organizer', src)
        self.assertIn('Sign In', src)
        self.assertNotIn('Logged out · Sign in', src)

    def test_dashboard_admin_detection_uses_rbac_roles_and_admin_permission(self):
        src = Path("src/App.jsx").read_text()
        self.assertIn('export function isAdminUser(user, rbac)', src)
        self.assertIn('const roles = normalizeList(rbac?.roles);', src)
        self.assertIn('const permissions = normalizeList(rbac?.permissions);', src)
        self.assertIn('roles.includes("admin")', src)
        self.assertIn('roles.includes("superadmin")', src)
        self.assertIn('permissions.includes("admin:read_dashboard")', src)
        self.assertIn('export function canAccessTextBookOrganizer(user, rbac, organizerEnabled, authChecked)', src)
        self.assertIn('isAdminUser(user, rbac) ||', src)
        self.assertIn('permissions.includes("book_organizer:create_self")', src)
        self.assertIn('return isAdmin ? <AdminOperationsDashboard /> : <MemberDashboard />;', src)

    def test_text_book_organizer_frontend_flag_defaults_on_for_production_only(self):
        src = Path("src/config.js").read_text()
        self.assertIn('const TEXT_BOOK_ORGANIZER_FLAG = import.meta.env.VITE_ENABLE_TEXT_BOOK_ORGANIZER;', src)
        self.assertIn('TEXT_BOOK_ORGANIZER_FLAG === undefined', src)
        self.assertIn('? !isDev', src)
        self.assertIn('["1", "true", "yes", "on"].includes(normalizedTextBookOrganizerFlag)', src)

    def test_home_and_library_keep_organizer_entry_points_permission_gated(self):
        home = Path("src/pages/Home.jsx").read_text()
        library = Path("src/pages/LibraryDecolonize.jsx").read_text()
        self.assertIn('Format a Book', home)
        self.assertIn('Upload Book Text', home)
        self.assertIn('authChecked && user', home)
        self.assertIn('ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer', home)
        self.assertIn('Text Book Organizer · Upload Book Text', library)
        self.assertIn('ENABLE_TEXT_BOOK_ORGANIZER && authChecked && canAccessOrganizer', library)


if __name__ == "__main__":
    unittest.main()
