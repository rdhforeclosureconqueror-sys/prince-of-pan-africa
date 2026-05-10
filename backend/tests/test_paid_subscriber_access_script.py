import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.paid_subscriber_access import (
    build_audit_row,
    effective_role_names,
    load_paid_user_emails,
)


class PaidSubscriberAccessScriptTests(unittest.TestCase):
    def test_load_paid_user_emails_from_csv_and_cli_dedupes_normalized_email(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "paid_users.csv"
            csv_path.write_text(
                "email,name\nPaid@Example.com,One\nother@example.com,Two\npaid@example.com,Duplicate\n",
                encoding="utf-8",
            )

            emails = load_paid_user_emails(str(csv_path), [" THIRD@EXAMPLE.COM ", "other@example.com"])

        self.assertEqual(emails, ["paid@example.com", "other@example.com", "third@example.com"])

    def test_effective_roles_fall_back_to_users_role_when_no_user_roles_exist(self):
        self.assertEqual(effective_role_names("subscriber", ()), {"subscriber"})
        self.assertEqual(effective_role_names("member", ("admin",)), {"admin"})

    def test_audit_row_marks_member_paid_user_as_missing_subscriber_access(self):
        user = SimpleNamespace(id=7, role="member", user_roles=[])

        row = build_audit_row("paid@example.com", user)

        self.assertEqual(row.status, "missing_subscriber_access")
        self.assertFalse(row.has_paid_access)
        self.assertTrue(row.needs_subscriber_access)

    def test_audit_row_accepts_subscriber_user_role(self):
        user = SimpleNamespace(
            id=8,
            role="member",
            user_roles=[SimpleNamespace(role=SimpleNamespace(name="subscriber"))],
        )

        row = build_audit_row("paid@example.com", user)

        self.assertEqual(row.status, "ok")
        self.assertTrue(row.has_paid_access)
        self.assertFalse(row.needs_subscriber_access)


if __name__ == "__main__":
    unittest.main()
