import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "../styles/globalNav.css";
import { AUTH_DEBUG, ENABLE_MUTUAL_AID_ALLOWLIST_SHELL, ENABLE_MUTUAL_AID_GOVERNANCE_CENTER, ENABLE_MUTUAL_AID_OPERATIONS_DASHBOARD, ENABLE_MUTUAL_AID_OVERVIEW, ENABLE_MUTUAL_AID_PILOT_UI_SHELL, ENABLE_TEXT_BOOK_ORGANIZER } from "../config";
import { PILOT_NAV_LINKS } from "../pilotScope";
import { getDashboardLabel, isAdminUser } from "../authz";

const EXTERNAL_LINKS = [
  { label: "Swahili Lesson", href: "/languages/swahili.html" },
  { label: "Yoruba Lesson", href: "/languages/yoruba.html" },
];

export default function GlobalNav({ user, rbac, canAccessOrganizer = false, authChecked = false }) {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const isAdmin = isAdminUser(user, rbac);

  useEffect(() => {
    if (!AUTH_DEBUG) return;

    const roles = Array.isArray(rbac?.roles) ? rbac.roles : [];
    const permissions = Array.isArray(rbac?.permissions) ? rbac.permissions : [];
    console.info("[auth-debug] global nav decision", {
      route: location.pathname,
      authChecked,
      email: user?.email || null,
      role: user?.role || null,
      roles,
      permissionCount: permissions.length,
      isAdmin,
      canAccessOrganizer,
      dashboardLabel: user ? getDashboardLabel(user, rbac) : null,
      visiblePrimaryAction: authChecked && user ? getDashboardLabel(user, rbac) : "Sign In",
    });
  }, [authChecked, user, rbac, isAdmin, canAccessOrganizer, location.pathname]);

  const handleToggle = () => setOpen((prev) => !prev);
  const closeMenu = () => setOpen(false);

  return (
    <header className="global-nav">
      <div className="global-nav__inner">
        <Link className="global-nav__logo" to="/" onClick={closeMenu}>
          🌌 Mufasa Universe
        </Link>

        <button
          type="button"
          className="global-nav__toggle"
          onClick={handleToggle}
          aria-expanded={open}
          aria-controls="global-nav-menu"
        >
          ☰ Menu
        </button>

        <nav id="global-nav-menu" className={`global-nav__links ${open ? "is-open" : ""}`}>
          {authChecked && user ? (
            <>
              {PILOT_NAV_LINKS.map((link) => {
                const label = link.to === "/dashboard" ? getDashboardLabel(user, rbac) : link.label;

                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    onClick={closeMenu}
                    className={location.pathname === link.to ? "global-nav__link is-active" : "global-nav__link"}
                  >
                    {label}
                  </Link>
                );
              })}

              {ENABLE_MUTUAL_AID_OVERVIEW ? (
                <Link
                  to="/mutual-aid"
                  onClick={closeMenu}
                  className={location.pathname === "/mutual-aid" ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Mutual Aid
                </Link>
              ) : null}

              {ENABLE_MUTUAL_AID_PILOT_UI_SHELL ? (
                <Link
                  to="/mutual-aid/request-preview"
                  onClick={closeMenu}
                  className={location.pathname.startsWith("/mutual-aid/") ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Mutual Aid Preview
                </Link>
              ) : null}


              {isAdmin && ENABLE_MUTUAL_AID_OPERATIONS_DASHBOARD ? (
                <Link
                  to="/admin/mutual-aid/dashboard"
                  onClick={closeMenu}
                  className={location.pathname === "/admin/mutual-aid/dashboard" ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Operations Dashboard
                </Link>
              ) : null}

              {isAdmin && ENABLE_MUTUAL_AID_GOVERNANCE_CENTER ? (
                <Link
                  to="/admin/mutual-aid/governance"
                  onClick={closeMenu}
                  className={location.pathname === "/admin/mutual-aid/governance" ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Governance Center
                </Link>
              ) : null}

              {isAdmin && ENABLE_MUTUAL_AID_ALLOWLIST_SHELL ? (
                <Link
                  to="/admin/mutual-aid/allowlist-preview"
                  onClick={closeMenu}
                  className={location.pathname === "/admin/mutual-aid/allowlist-preview" ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Aid Allowlist Preview
                </Link>
              ) : null}

              {isAdmin && ENABLE_MUTUAL_AID_PILOT_UI_SHELL ? (
                <Link
                  to="/admin/mutual-aid/review-preview"
                  onClick={closeMenu}
                  className={location.pathname.startsWith("/admin/mutual-aid/") ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Aid Admin Preview
                </Link>
              ) : null}

              {ENABLE_TEXT_BOOK_ORGANIZER && canAccessOrganizer ? (
                <Link
                  to="/library/organizer"
                  onClick={closeMenu}
                  className={location.pathname === "/library/organizer" ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Text Book Organizer
                </Link>
              ) : null}

              {isAdmin ? (
                <Link
                  to="/ops/verification"
                  onClick={closeMenu}
                  className={location.pathname === "/ops/verification" ? "global-nav__link is-active" : "global-nav__link"}
                >
                  Verification Center
                </Link>
              ) : null}

              <div className="global-nav__auth-state">
                <span>Logged in as: {user.email}</span>
              </div>

              {EXTERNAL_LINKS.map((link) => (
                <a key={link.href} href={link.href} className="global-nav__link" onClick={closeMenu}>
                  {link.label}
                </a>
              ))}
            </>
          ) : (
            <div className="global-nav__auth-state">
              <Link to="/?auth=login" onClick={closeMenu} className="global-nav__link">
                Sign In
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
