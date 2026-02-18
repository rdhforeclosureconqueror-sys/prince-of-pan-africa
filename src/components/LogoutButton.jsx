import React from "react";

export default function LogoutButton() {
  const handleLogout = () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  };

  return (
    <button onClick={handleLogout}>
      Logout
    </button>
  );
}
