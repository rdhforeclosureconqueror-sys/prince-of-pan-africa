import json
import subprocess
import textwrap
import unittest


class FrontendAuthzHelperBehaviorTests(unittest.TestCase):
    def test_navigation_access_matrix(self):
        script = textwrap.dedent(
            """
            import { canAccessMemberDashboard, canAccessTextBookOrganizer, isAdminUser } from './src/authz.js';

            const featureEnabled = true;
            const authChecked = true;
            const cases = {
              admin: {
                user: { id: 1, role: 'member', is_admin: false },
                rbac: { roles: ['admin'], permissions: ['admin:read_dashboard'] },
              },
              subscriber: {
                user: { id: 2, role: 'subscriber', is_admin: false },
                rbac: { roles: ['subscriber'], permissions: ['member:read_overview_self', 'book_organizer:create_self'] },
              },
              member: {
                user: { id: 3, role: 'member', is_admin: false },
                rbac: { roles: ['member'], permissions: ['member:read_overview_self'] },
              },
              loggedOut: { user: null, rbac: { roles: [], permissions: [] } },
            };

            const result = Object.fromEntries(Object.entries(cases).map(([name, value]) => [name, {
              admin: isAdminUser(value.user, value.rbac),
              dashboard: canAccessMemberDashboard(value.user, value.rbac),
              organizer: canAccessTextBookOrganizer(value.user, value.rbac, featureEnabled, authChecked),
            }]));
            console.log(JSON.stringify(result));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)

        self.assertEqual(result["admin"], {"admin": True, "dashboard": True, "organizer": True})
        self.assertEqual(result["subscriber"], {"admin": False, "dashboard": True, "organizer": True})
        self.assertEqual(result["member"], {"admin": False, "dashboard": True, "organizer": False})
        self.assertEqual(result["loggedOut"], {"admin": False, "dashboard": False, "organizer": False})


if __name__ == "__main__":
    unittest.main()
