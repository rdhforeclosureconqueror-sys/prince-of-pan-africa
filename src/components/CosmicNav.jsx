// ✅ src/components/CosmicNav.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./cosmicNav.css";

export default function CosmicNav() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const pages = [
    { name: "Home", path: "/" },
    { name: "Timeline", path: "/timeline" },
    { name: "Calendar", path: "/calendar" },
    { name: "Journal", path: "/journal" },
    { name: "Ledger", path: "/ledger" },
    { name: "Ledger V2", path: "/ledger-v2" },
    { name: "Pan-Africa’s Got Talent", path: "/pagt" },
    { name: "Admin", path: "/admin" },
  ];

  function goTo(path) {
    navigate(path);
    setOpen(false);
  }

  return (
    <div className="cosmic-nav">
      <div className="logo" onClick={() => navigate("/")}>
        🦁 SimbaNet
      </div>

      <div className="menu">
        <button
          className="menu-button"
          onClick={() => setOpen((prev) => !prev)}
        >
          ☰ Menu
        </button>

        {open && (
          <div className="dropdown">
            {pages.map((p, i) => (
              <div
                key={i}
                className="dropdown-item"
                onClick={() => goTo(p.path)}
              >
                {p.name}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
