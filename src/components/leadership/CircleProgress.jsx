import React from "react";

export default function CircleProgress({ value, label, image }) {
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference - (clamped / 100) * circumference;

  return (
    <div className="circle-progress-card">
      {image ? <img src={image} alt={label} className="role-image" /> : null}
      <svg width="100" height="100" viewBox="0 0 100 100" aria-label={`${label} ${clamped}%`}>
        <circle cx="50" cy="50" r={radius} className="circle-bg" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          className="circle-fill"
          strokeDasharray={circumference}
          strokeDashoffset={dash}
        />
      </svg>
      <strong>{label}</strong>
      <span>{clamped}%</span>
    </div>
  );
}
