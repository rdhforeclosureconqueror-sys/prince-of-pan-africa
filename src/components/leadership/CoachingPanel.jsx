import React from "react";

export default function CoachingPanel({ coaching }) {
  return (
    <section className="coaching-panel">
      <h3>Coaching Guidance</h3>
      <p>{coaching}</p>
    </section>
  );
}
