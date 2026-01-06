import React from "react";
import { Link } from "react-router-dom";

const NavBar = () => {
  return (
    <nav className="p-4 bg-gray-900 text-white flex gap-4">
      <Link to="/">Home</Link>
      <Link to="/dashboard">Dashboard</Link>
      <Link to="/fitness">Fitness</Link>
      <Link to="/study">Study</Link>
      <Link to="/journal">Journal</Link>
      <Link to="/language">Language</Link>
      <Link to="/ledger">Ledger</Link>
    </nav>
  );
};

export default NavBar;
