import React, { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE_URL, AUTH_DEBUG, ENABLE_TEXT_BOOK_ORGANIZER } from "../config";
import { api } from "../api/api";
import { canAccessTextBookOrganizer, isAdminUser } from "../authz";

const REDACTED = "[redacted]";
const SENSITIVE_KEY_PATTERN = /(cookie|token|secret|signature|password|hash|session)/i;

function sanitizeDebugValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeDebugValue(item));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, entryValue]) => [
        key,
        SENSITIVE_KEY_PATTERN.test(key) ? REDACTED : sanitizeDebugValue(entryValue),
      ]),
    );
  }

  return value;
}

function formatJson(value) {
  return JSON.stringify(value ?? null, null, 2);
}

function getBackendIsAdmin(data) {
  if (!data || typeof data !== "object") return null;
  if (typeof data.is_admin === "boolean") return data.is_admin;
  if (typeof data.user?.is_admin === "boolean") return data.user.is_admin;
  if (typeof data.admin === "boolean") return data.admin;
  return null;
}

function AuthDebugRow({ label, children }) {
  return (
    <div className="auth-debug-row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

export default function AuthDebugPage({ authChecked, user, rbac }) {
  const [backendResult, setBackendResult] = useState({ loading: false, data: null, error: null, status: null });

  const frontendIsAdmin = useMemo(() => isAdminUser(user, rbac), [user, rbac]);
  const organizerAccess = useMemo(
    () => canAccessTextBookOrganizer(user, rbac, ENABLE_TEXT_BOOK_ORGANIZER, authChecked),
    [user, rbac, authChecked],
  );

  const callBackendDebug = useCallback(async () => {
    if (!AUTH_DEBUG) return;

    setBackendResult({ loading: true, data: null, error: null, status: null });

    try {
      const data = await api("/auth/debug/me", {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      setBackendResult({ loading: false, data: sanitizeDebugValue(data), error: null, status: 200 });
    } catch (error) {
      setBackendResult({
        loading: false,
        data: sanitizeDebugValue(error?.payload || null),
        error: error?.message || "Backend auth debug request failed.",
        status: error?.status || null,
      });
    }
  }, []);

  useEffect(() => {
    callBackendDebug();
  }, [callBackendDebug]);

  const backendIsAdmin = getBackendIsAdmin(backendResult.data);
  const diagnostics = [];

  if (backendResult.status === 401) {
    diagnostics.push("Backend returned 401: the mufasa_session cookie is not reaching the backend API through this frontend request.");
  }

  if (backendIsAdmin === false) {
    diagnostics.push("Backend returned is_admin=false: the backend does not recognize this account as an admin.");
  }

  if (backendIsAdmin === true && !frontendIsAdmin) {
    diagnostics.push("Backend returned is_admin=true but the frontend admin helper returned false: frontend auth helper/hydration mismatch.");
  }

  if (backendIsAdmin === true && frontendIsAdmin) {
    diagnostics.push("Backend and frontend both recognize this account as admin.");
  }

  if (!AUTH_DEBUG) {
    return (
      <main className="library-shell auth-debug-page">
        <section className="library-inner cosmic-readable-shell">
          <h1>Auth debug disabled.</h1>
          <p>Enable this temporary page with VITE_AUTH_DEBUG=true, ?authDebug=1, or localStorage.authDebug=1.</p>
        </section>
      </main>
    );
  }

  const roles = Array.isArray(rbac?.roles) ? rbac.roles : [];
  const permissions = Array.isArray(rbac?.permissions) ? rbac.permissions : [];

  return (
    <main className="library-shell auth-debug-page">
      <section className="library-inner cosmic-readable-shell">
        <h1>Auth Debug</h1>
        <p>
          Temporary protected diagnostic view. This page uses the shared <code>api()</code> helper to call <code>/auth/debug/me</code> with credentials included.
        </p>

        <div className="library-actions">
          <button type="button" className="library-pill library-pill--green" onClick={callBackendDebug} disabled={backendResult.loading}>
            {backendResult.loading ? "Checking..." : "Re-check backend auth"}
          </button>
        </div>

        {diagnostics.length > 0 && (
          <section aria-labelledby="auth-debug-diagnosis">
            <h2 id="auth-debug-diagnosis">Diagnosis</h2>
            <ul>
              {diagnostics.map((diagnostic) => (
                <li key={diagnostic}>{diagnostic}</li>
              ))}
            </ul>
          </section>
        )}

        <section aria-labelledby="auth-debug-frontend">
          <h2 id="auth-debug-frontend">Frontend auth state</h2>
          <dl>
            <AuthDebugRow label="Current frontend origin">{window.location.origin}</AuthDebugRow>
            <AuthDebugRow label="API base URL">{API_BASE_URL}</AuthDebugRow>
            <AuthDebugRow label="authChecked">{String(Boolean(authChecked))}</AuthDebugRow>
            <AuthDebugRow label="user.email">{user?.email || "null"}</AuthDebugRow>
            <AuthDebugRow label="user.role">{user?.role || "null"}</AuthDebugRow>
            <AuthDebugRow label="rbac.roles"><pre>{formatJson(roles)}</pre></AuthDebugRow>
            <AuthDebugRow label="rbac.permissions"><pre>{formatJson(permissions)}</pre></AuthDebugRow>
            <AuthDebugRow label="isAdminUser(user, rbac)">{String(frontendIsAdmin)}</AuthDebugRow>
            <AuthDebugRow label="canAccessTextBookOrganizer(...)">{String(organizerAccess)}</AuthDebugRow>
          </dl>
        </section>

        <section aria-labelledby="auth-debug-backend">
          <h2 id="auth-debug-backend">Backend /auth/debug/me</h2>
          <dl>
            <AuthDebugRow label="Status">
              {backendResult.loading ? "Loading..." : backendResult.status || "No response status"}
            </AuthDebugRow>
            {backendResult.error && <AuthDebugRow label="Error">{backendResult.error}</AuthDebugRow>}
            <AuthDebugRow label="Sanitized response">
              <pre>{formatJson(backendResult.data)}</pre>
            </AuthDebugRow>
          </dl>
        </section>

        <p><strong>Safety:</strong> cookies, tokens, signatures, secrets, sessions, password fields, and hashes are redacted and should not be displayed here.</p>
      </section>
    </main>
  );
}
