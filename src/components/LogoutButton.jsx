import React from "react";
import { api } from "../api/api";

export default function LogoutButton() {
  const handleLogout = async () => {
    try {
      const data = await api("/auth/logout", { method: "POST" });
      if (data.ok) {
        window.location.href = "/";
      } else {
        alert("Logout failed. Please try again.");
      }
    } catch (err) {
      console.error("Logout error:", err);
      alert("Could not log out.");
    }
  };

  return (
    <button className="logout-btn" onClick={handleLogout}>
      🚪 Logout
    </button>
  );
}
