import React from "react";
import ReactDOM from "react-dom/client";
import MufasaCoach from "./pages/MufasaCoach";
import "../src/styles/fitness.css";

async function initApp() {
  // small delay to let TFJS load
  await new Promise((r) => setTimeout(r, 1800));
  const loader = document.getElementById("loader");
  if (loader) loader.style.display = "none";

  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <MufasaCoach />
    </React.StrictMode>
  );
}

initApp();
