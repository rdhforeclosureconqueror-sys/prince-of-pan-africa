#!/usr/bin/env bash
set -u

BASE_URL="${BASE_URL:-}"
ADMIN_EMAIL="${ADMIN_EMAIL:-}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
MEMBER_EMAIL="${MEMBER_EMAIL:-}"
MEMBER_PASSWORD="${MEMBER_PASSWORD:-}"

if [[ -z "$BASE_URL" ]]; then
  echo "FAIL: BASE_URL is required (e.g. https://mufasa-knowledge-bank.onrender.com)"
  exit 1
fi

BASE_URL="${BASE_URL%/}"
TMP_DIR="$(mktemp -d)"
ADMIN_COOKIE_JAR="$TMP_DIR/admin_cookies.txt"
MEMBER_COOKIE_JAR="$TMP_DIR/member_cookies.txt"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass(){ echo "PASS: $1"; PASS_COUNT=$((PASS_COUNT+1)); }
fail(){ echo "FAIL: $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }
warn(){ echo "WARN: $1"; WARN_COUNT=$((WARN_COUNT+1)); }

http_code(){
  local method="$1" url="$2" data="${3:-}" cookie_jar="${4:-}" out_body="${5:-}"
  local args=(-sS -o "$out_body" -w "%{http_code}" -X "$method" "$url")
  if [[ -n "$cookie_jar" ]]; then
    args+=( -c "$cookie_jar" -b "$cookie_jar" )
  fi
  if [[ -n "$data" ]]; then
    args+=( -H "Content-Type: application/json" --data "$data" )
  fi
  curl "${args[@]}"
}

require_status(){
  local name="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    pass "$name (status $actual)"
  else
    fail "$name (expected $expected got $actual)"
  fi
}

echo "Running internal pilot smoke test against: $BASE_URL"

# 1) /health status
health_body="$TMP_DIR/health.json"
health_code="$(http_code GET "$BASE_URL/health" "" "" "$health_body")" || health_code="000"
if [[ "$health_code" == "200" ]]; then
  status_val="$(python3 - <<'PY' "$health_body"
import json,sys
try:
    data=json.load(open(sys.argv[1]))
    print(data.get('status',''))
except Exception:
    print('')
PY
)"
  if [[ "$status_val" == "ok" || "$status_val" == "degraded" ]]; then
    pass "GET /health returns status '$status_val'"
  else
    fail "GET /health returned unexpected status field: '$status_val'"
  fi
else
  fail "GET /health (expected 200 got $health_code)"
fi

# 2) Unauthenticated admin route should be 401
admin_unauth_body="$TMP_DIR/admin_unauth.json"
admin_unauth_code="$(http_code GET "$BASE_URL/admin/overview" "" "" "$admin_unauth_body")" || admin_unauth_code="000"
require_status "Unauthenticated GET /admin/overview" "401" "$admin_unauth_code"

# 3) Login/admin checks if admin creds provided
if [[ -n "$ADMIN_EMAIL" && -n "$ADMIN_PASSWORD" ]]; then
  admin_login_body="$TMP_DIR/admin_login.json"
  payload=$(printf '{"email":"%s","password":"%s"}' "$ADMIN_EMAIL" "$ADMIN_PASSWORD")
  admin_login_code="$(http_code POST "$BASE_URL/auth/login" "$payload" "$ADMIN_COOKIE_JAR" "$admin_login_body")" || admin_login_code="000"
  require_status "POST /auth/login (admin)" "200" "$admin_login_code"

  if grep -qi "session" "$ADMIN_COOKIE_JAR"; then
    pass "Signed session cookie issued for admin login"
  else
    fail "No session cookie found in admin cookie jar"
  fi

  admin_auth_body="$TMP_DIR/admin_auth.json"
  admin_auth_code="$(http_code GET "$BASE_URL/admin/overview" "" "$ADMIN_COOKIE_JAR" "$admin_auth_body")" || admin_auth_code="000"
  require_status "Authenticated admin GET /admin/overview" "200" "$admin_auth_code"
else
  warn "Skipping admin login/admin-auth checks (set ADMIN_EMAIL and ADMIN_PASSWORD)"
fi

# 4) /system/verification requires auth/permission
system_unauth_body="$TMP_DIR/system_unauth.json"
system_unauth_code="$(http_code GET "$BASE_URL/system/verification" "" "" "$system_unauth_body")" || system_unauth_code="000"
if [[ "$system_unauth_code" == "401" || "$system_unauth_code" == "403" ]]; then
  pass "GET /system/verification is protected (status $system_unauth_code)"
else
  fail "GET /system/verification should require auth/permission (got $system_unauth_code)"
fi

# 5) member route check if member creds provided
if [[ -n "$MEMBER_EMAIL" && -n "$MEMBER_PASSWORD" ]]; then
  member_login_body="$TMP_DIR/member_login.json"
  member_payload=$(printf '{"email":"%s","password":"%s"}' "$MEMBER_EMAIL" "$MEMBER_PASSWORD")
  member_login_code="$(http_code POST "$BASE_URL/auth/login" "$member_payload" "$MEMBER_COOKIE_JAR" "$member_login_body")" || member_login_code="000"
  require_status "POST /auth/login (member)" "200" "$member_login_code"

  if grep -qi "session" "$MEMBER_COOKIE_JAR"; then
    pass "Signed session cookie issued for member login"
  else
    fail "No session cookie found in member cookie jar"
  fi

  member_overview_body="$TMP_DIR/member_overview.json"
  member_overview_code="$(http_code GET "$BASE_URL/member/overview" "" "$MEMBER_COOKIE_JAR" "$member_overview_body")" || member_overview_code="000"
  require_status "Authenticated member GET /member/overview" "200" "$member_overview_code"
else
  warn "Skipping member route checks (set MEMBER_EMAIL and MEMBER_PASSWORD)"
fi

echo
echo "Summary: PASS=$PASS_COUNT FAIL=$FAIL_COUNT WARN=$WARN_COUNT"
if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi
exit 0
