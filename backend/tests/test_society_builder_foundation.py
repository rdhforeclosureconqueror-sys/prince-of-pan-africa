import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class SocietyBuilderFoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "society_builder.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        os.environ["ALLOW_INSECURE_DEV_SESSION_SECRET"] = "true"
        os.environ["APP_ENV"] = "test"
        os.environ["SOCIETY_BUILDER_ENABLED"] = "true"

        import app.config as config_module
        import app.database as database_module
        import app.models as models_module
        import app.authz as authz_module
        import app.services.society_builder as service_module

        importlib.reload(config_module)
        importlib.reload(database_module)
        importlib.reload(models_module)
        importlib.reload(authz_module)
        importlib.reload(service_module)
        database_module.init_db()
        self.dbm = database_module
        self.models = models_module
        self.authz = authz_module
        self.service = service_module
        db = self.dbm.SessionLocal()
        try:
            self.authz.seed_rbac_defaults(db)
            self.user = self.models.User(email="member@example.com", password_hash="x", role="community_member")
            self.admin = self.models.User(email="admin@example.com", password_hash="x", role="admin")
            self.other = self.models.User(email="other@example.com", password_hash="x", role="community_member")
            db.add_all([self.user, self.admin, self.other])
            db.commit()
            self.authz.seed_rbac_defaults(db)
            db.refresh(self.user); db.refresh(self.admin); db.refresh(self.other)
            self.user_id, self.admin_id, self.other_id = self.user.id, self.admin.id, self.other.id
        finally:
            db.close()

        import app.main as main_module
        importlib.reload(main_module)
        self.client = TestClient(main_module.app)
        from app.session import build_session_cookie_value
        self.member_cookie = {"mufasa_session": build_session_cookie_value(self.user_id)}
        self.admin_cookie = {"mufasa_session": build_session_cookie_value(self.admin_id)}
        self.other_cookie = {"mufasa_session": build_session_cookie_value(self.other_id)}

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_society(self, cookie=None, **overrides):
        payload = {"name": "Harlem Care Circle", "type": "Neighborhood", "first_focus": "Emergency aid", "chapter_level": "local_society", "geographic_scope": "city"}
        payload.update(overrides)
        res = self.client.post("/society-builder/societies", json=payload, cookies=cookie or self.member_cookie)
        self.assertEqual(res.status_code, 200, res.text)
        return res.json()["society"]

    def test_feature_flag_disabled_behavior(self):
        os.environ["SOCIETY_BUILDER_ENABLED"] = "false"
        res = self.client.get("/society-builder/main-hub")
        self.assertEqual(res.status_code, 404)
        os.environ["SOCIETY_BUILDER_ENABLED"] = "true"

    def test_simba_main_hub_idempotent_seed(self):
        db = self.dbm.SessionLocal()
        try:
            a = self.service.seed_simba_main_hub(db)
            b = self.service.seed_simba_main_hub(db)
            self.assertEqual(a.id, b.id)
            self.assertEqual(db.query(self.models.Society).filter_by(is_main_hub=True).count(), 1)
            self.assertEqual(a.name, "Simba Mutual Aid Society")
        finally:
            db.close()

    def test_society_creation_and_hierarchy(self):
        hub = self.client.get("/society-builder/main-hub").json()["main_hub"]
        child = self.create_society(parent_society_id=hub["id"])
        self.assertEqual(child["parent_society_id"], hub["id"])
        self.assertEqual(child["root_society_id"], hub["id"])

    def test_local_society_admin_cannot_manage_main_hub(self):
        hub = self.client.get("/society-builder/main-hub").json()["main_hub"]
        res = self.client.patch(f"/society-builder/societies/{hub['id']}", json={"name": "Bad"}, cookies=self.member_cookie)
        self.assertEqual(res.status_code, 403)

    def test_chapter_application_flow_and_approval_permission(self):
        s = self.create_society()
        res = self.client.post(f"/society-builder/societies/{s['id']}/apply-chapter", cookies=self.member_cookie)
        self.assertEqual(res.json()["society"]["affiliation_status"], "pending_review")
        forbidden = self.client.post(f"/society-builder/admin/chapter-applications/{s['id']}/approve", cookies=self.member_cookie)
        self.assertEqual(forbidden.status_code, 403)
        approved = self.client.post(f"/society-builder/admin/chapter-applications/{s['id']}/approve", cookies=self.admin_cookie)
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["society"]["affiliation_status"], "approved")

    def test_blueprint_audit_logic(self):
        s = self.create_society()
        payload = {"trust_score": 2, "relationships_score": 3, "mutual_aid_score": 3, "organization_score": 2, "institutions_score": 1, "businesses_score": 5, "property_score": 1, "community_wealth_score": 1, "political_power_score": 5, "notes": "x"}
        res = self.client.post(f"/society-builder/societies/{s['id']}/blueprint-audit", json=payload, cookies=self.member_cookie)
        data = res.json()["blueprint_audit"]
        self.assertEqual(data["weakest_area"], "Institutions")
        self.assertEqual(data["strongest_area"], "Businesses")
        self.assertTrue(data["warning"])

    def test_first_ten_critical_role_warnings(self):
        s = self.create_society()
        res = self.client.post(f"/society-builder/societies/{s['id']}/first-ten", json={"name": "Amina", "role": "Facilitator"}, cookies=self.member_cookie)
        summary = res.json()["summary"]
        self.assertIn("Treasurer", summary["missing_critical_roles"])
        self.assertIn("Recordkeeper", summary["missing_critical_roles"])
        self.assertTrue(summary["warning"])

    def test_purpose_generation_and_covenant_save(self):
        s = self.create_society()
        res = self.client.post(f"/society-builder/societies/{s['id']}/purpose", json={"community_served": "elders", "recurring_problem": "missed rides", "first_focus": "Emergency aid", "member_contribution": "coordinate weekly check-ins", "day_100_goal": "a reliable care rhythm"}, cookies=self.member_cookie)
        self.assertIn("We are forming a mutual aid society", res.json()["purpose"]["purpose_statement"])
        vague = self.client.post(f"/society-builder/societies/{s['id']}/purpose", json={"community_served": "help the community"}, cookies=self.member_cookie)
        self.assertTrue(vague.json()["purpose"]["refinement_prompt"])
        cov = self.client.post(f"/society-builder/societies/{s['id']}/covenant", json={"covenant_text": "We will show up consistently.", "version": "v1", "status": "Active", "accepted_by_members": []}, cookies=self.member_cookie)
        self.assertEqual(cov.json()["covenant"]["status"], "Active")

    def test_stage_checks_and_audit_logs(self):
        s = self.create_society()
        self.client.post(f"/society-builder/societies/{s['id']}/blueprint-audit", json={"trust_score":3,"relationships_score":3,"mutual_aid_score":3,"organization_score":3,"institutions_score":3,"businesses_score":1,"property_score":1,"community_wealth_score":1,"political_power_score":1}, cookies=self.member_cookie)
        res = self.client.post(f"/society-builder/societies/{s['id']}/advance-stage", json={"target_stage": "Forming"}, cookies=self.member_cookie)
        self.assertTrue(res.json()["advanced"])
        self.client.post(f"/society-builder/societies/{s['id']}/purpose", json={"community_served":"neighbors","recurring_problem":"emergencies","first_focus":"Emergency aid"}, cookies=self.member_cookie)
        for name, role in [("A", "Facilitator"), ("B", "Member"), ("C", "Member")]:
            self.client.post(f"/society-builder/societies/{s['id']}/first-ten", json={"name": name, "role": role}, cookies=self.member_cookie)
        res2 = self.client.post(f"/society-builder/societies/{s['id']}/advance-stage", json={"target_stage": "Foundation Phase"}, cookies=self.member_cookie)
        self.assertTrue(res2.json()["advanced"])
        override_bad = self.client.post(f"/society-builder/admin/societies/{s['id']}/stage-override", json={"target_stage": "Exploring", "explanation": ""}, cookies=self.admin_cookie)
        self.assertEqual(override_bad.status_code, 422)
        override = self.client.post(f"/society-builder/admin/societies/{s['id']}/stage-override", json={"target_stage": "Forming", "explanation": "Correction"}, cookies=self.admin_cookie)
        self.assertEqual(override.status_code, 200)
        db = self.dbm.SessionLocal()
        try:
            actions = {a for (a,) in db.query(self.models.MutualAidAuditLog.action).filter(self.models.MutualAidAuditLog.entity_id == s['id']).all()}
            self.assertIn("lifecycle_stage_changed", actions)
            self.assertIn("lifecycle_stage_overridden", actions)
        finally:
            db.close()

    def test_parent_hub_summary_does_not_expose_private_notes(self):
        hub = self.client.get("/society-builder/main-hub").json()["main_hub"]
        s = self.create_society(parent_society_id=hub["id"])
        self.client.post(f"/society-builder/societies/{s['id']}/first-ten", json={"name":"Private Person","role":"Member","notes":"private hardship details"}, cookies=self.member_cookie)
        self.client.post(f"/society-builder/societies/{s['id']}/apply-chapter", cookies=self.member_cookie)
        self.client.post(f"/society-builder/admin/chapter-applications/{s['id']}/approve", cookies=self.admin_cookie)
        data = self.client.get("/society-builder/main-hub").json()
        text = str(data)
        self.assertIn("member_counts", text)
        self.assertNotIn("private hardship details", text)
        self.assertNotIn("Private Person", text)


if __name__ == "__main__":
    unittest.main()
