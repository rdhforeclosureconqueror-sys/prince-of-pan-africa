// ✅ src/index.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// 🧩 Global styles (must load first)
import "./styles/theme.css";
import "./styles/universe.css";

// 🧩 Shell + UI layers
import "./styles/MufasaShell.css";
import "./styles/dashboard.css";
import "./styles/achievementToast.css";
import "./styles/xpOverlay.css";

// 🧩 Section-specific
import "./v2-ledger/ledgerV2.css";
import "./admin/admin.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
