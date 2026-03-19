import React from "react";

export default function RoleMeter({ label, value }) {
  return (
    <div className="role-meter">
      <div className="role-meter__head">
        <span>{label}</span>
        <strong>{value}%</strong>
      </div>
      <div className="role-meter__track">
        <div className="role-meter__fill" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}
