import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "../styles/globalNav.css";
import { PILOT_NAV_LINKS } from "../pilotScope";

const EXTERNAL_LINKS = [
  { label: "Swahili Lesson", href: "/languages/swahili.html" },
  { label: "Yoruba Lesson", href: "/languages/yoruba.html" },
];

export default function GlobalNav({ isAdmin }) {
  const [open, setOpen] = useState(false);
  const location = useLocation();

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
          {PILOT_NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={closeMenu}
              className={location.pathname === link.to ? "global-nav__link is-active" : "global-nav__link"}
            >
              {link.label}
            </Link>
          ))}

          {isAdmin ? (
            <Link
              to="/ops/verification"
              onClick={closeMenu}
              className={location.pathname === "/ops/verification" ? "global-nav__link is-active" : "global-nav__link"}
            >
              Verification Center
            </Link>
          ) : null}

          {EXTERNAL_LINKS.map((link) => (
            <a key={link.href} href={link.href} className="global-nav__link" onClick={closeMenu}>
              {link.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
