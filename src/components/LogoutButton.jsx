import React from "react";

export default function LogoutButton() {
  const handleLogout = async () => {
    try {
      const res = await fetch("/auth/logout", {
        method: "POST",
        credentials: "include",
      });
      const data = await res.json();
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
