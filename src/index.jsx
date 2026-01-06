// ✅ src/index.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// 🧩 Import all global styles here
import "./styles/themes.css";
import "./styles/universe.css";
import "./styles/MufasaShell.css";
import "./styles/dashboard.css";
import "./styles/achievementToast.css";
import "./styles/xpOverlay.css";
import "./styles/ledgerV2.css";
import "./styles/admin.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
