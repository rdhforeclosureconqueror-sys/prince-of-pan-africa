import React from "react";

export default function CoachingPanel({ coaching, insights }) {
  return (
    <section className="coaching-panel">
      <h3>Coaching Guidance</h3>
      <p>{coaching}</p>
      {insights ? (
        <ul>
          {insights.primary ? <li><strong>Primary insight:</strong> {insights.primary}</li> : null}
          {insights.growth ? <li><strong>Growth insight:</strong> {insights.growth}</li> : null}
          {insights.shadow ? <li><strong>Shadow insight:</strong> {insights.shadow}</li> : null}
        </ul>
      ) : null}
    </section>
  );
}
