import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import LeadershipForm from "../components/leadership/LeadershipForm";
import { submitLeadershipAssessment } from "../services/leadershipService";
import "../styles/leadership.css";

function generateUserId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `leader-${Date.now()}`;
}

export default function LeadershipAssessmentPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(answers) {
    setLoading(true);
    setError("");
    try {
      const userId = generateUserId();
      const result = await submitLeadershipAssessment({ userId, answers });
      navigate(`/results?userId=${encodeURIComponent(result.userId)}`, {
        state: { result },
      });
    } catch (err) {
      setError(err.message || "We could not submit your assessment. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="leadership-page">
      <header>
        <h1>Leadership Assessment</h1>
        <p>Complete 30 prompts to reveal your primary, secondary, growth, and shadow leadership roles.</p>
      </header>

      {error ? <div className="leadership-error">{error}</div> : null}
      <LeadershipForm onSubmit={handleSubmit} loading={loading} />
    </main>
  );
}
