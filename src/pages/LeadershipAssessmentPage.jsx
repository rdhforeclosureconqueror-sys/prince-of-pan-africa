import React, { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import LeadershipForm from "../components/leadership/LeadershipForm";
import { submitLeadershipAssessment } from "../services/leadershipService";
import "../styles/leadership.css";

export default function LeadershipAssessmentPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(answers) {
    setLoading(true);
    setError("");
    try {
      const result = await submitLeadershipAssessment({
        answers,
        userId: searchParams.get("userId") || undefined,
        accountId: searchParams.get("accountId") || undefined,
        parentId: searchParams.get("parentId") || undefined,
        childId: searchParams.get("childId") || undefined,
      });

      console.info("[leadership-trace] route transition", {
        to: "/results",
        userId: result.userId,
        assessmentId: result.assessmentId,
      });

      navigate(`/results?userId=${encodeURIComponent(result.userId)}`, {
        state: { assessmentId: result.assessmentId, submissionId: result.submissionId },
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
