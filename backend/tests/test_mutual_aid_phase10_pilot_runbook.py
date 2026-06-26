from tests.session_test_utils import session_cookie
from tests.test_mutual_aid_pilot_launch_lock import build_app, seed_user


def get_runbook(client, user_id):
    return client.get("/mutual-aid/admin/pilot-runbook/verification", cookies=session_cookie(user_id))


def test_phase10_runbook_non_admin_denied():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        assert get_runbook(client, member_id).status_code == 403
    finally:
        tmp.cleanup()


def test_phase10_runbook_fails_if_launch_lock_fails():
    tmp, database, models, client = build_app(flags=False)
    try:
        admin_id = seed_user(database, models, "admin")
        response = get_runbook(client, admin_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "no-go"
        assert data["phase9_launch_lock"]["status"] == "no-go"
        assert any(blocker["key"] == "required_flags_present" for blocker in data["blockers"])
    finally:
        tmp.cleanup()


def test_phase10_runbook_passes_only_when_readiness_and_launch_lock_pass():
    tmp, database, models, client = build_app()
    try:
        admin_id = seed_user(database, models, "admin")
        response = get_runbook(client, admin_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "go"
        assert data["go_no_go_result"] == "GO"
        assert data["phase8_readiness"]["status"] == "pass"
        assert data["phase9_launch_lock"]["status"] == "go"
        assert "ENABLE_MUTUAL_AID_PAYMENTS=false" in data["required_flags"]
    finally:
        tmp.cleanup()


def test_phase10_payments_remain_disabled_and_no_money_routes_exist():
    tmp, database, models, client = build_app()
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_runbook(client, admin_id).json()
        assert any(item["key"] == "payments_disabled" and item["passed"] for item in data["operator_checklist"])
        route_paths = {route.path.lower() for route in client.app.routes}
        assert not any("mutual-aid" in path and any(term in path for term in ("payment", "payout", "wallet")) for path in route_paths)
    finally:
        tmp.cleanup()
