from tests.session_test_utils import session_cookie
from tests.test_mutual_aid_pilot_launch_lock import build_app, seed_user


def get_smoke_tests(client, user_id):
    return client.get("/mutual-aid/admin/pilot-smoke-tests/verification", cookies=session_cookie(user_id))


def test_phase11_smoke_tests_non_admin_denied():
    tmp, database, models, client = build_app()
    try:
        member_id = seed_user(database, models)
        assert get_smoke_tests(client, member_id).status_code == 403
    finally:
        tmp.cleanup()


def test_phase11_smoke_tests_fail_if_payments_enabled():
    tmp, database, models, client = build_app(payments="true")
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_smoke_tests(client, admin_id).json()
        assert data["status"] == "fail"
        assert any(blocker["key"] == "payments_disabled" for blocker in data["blockers"])
    finally:
        tmp.cleanup()


def test_phase11_smoke_tests_fail_if_required_phase_flag_missing():
    tmp, database, models, client = build_app(flags=False)
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_smoke_tests(client, admin_id).json()
        assert data["status"] == "fail"
        assert any(blocker["key"] == "required_phase_flag_missing" for blocker in data["blockers"])
    finally:
        tmp.cleanup()


def test_phase11_smoke_tests_pass_when_pilot_safe_flags_are_correct():
    tmp, database, models, client = build_app()
    try:
        admin_id = seed_user(database, models, "admin")
        response = get_smoke_tests(client, admin_id)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "pass"
        assert data["passed"] is True
        assert data["read_only"] is True
        assert data["persisted"] is False
        assert data["fund_status"] == "Building Toward Activation"
        assert data["activation_threshold"] == 20000
        assert data["blockers"] == []
        assert "No live submissions" in data["pilot_safe_warnings"][0]
        assert "does not persist" in data["no_persistence_warning"]
    finally:
        tmp.cleanup()


def test_phase11_smoke_tests_confirm_no_payment_payout_wallet_routes():
    tmp, database, models, client = build_app()
    try:
        admin_id = seed_user(database, models, "admin")
        data = get_smoke_tests(client, admin_id).json()
        assert data["money_route_findings"] == []
        route_paths = {route.path.lower() for route in client.app.routes}
        assert not any("mutual-aid" in path and any(term in path for term in ("payment", "payout", "wallet")) for path in route_paths)
    finally:
        tmp.cleanup()
