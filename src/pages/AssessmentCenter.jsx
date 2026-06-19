import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createAssessmentTransferToken, getAssessmentCatalog, getAssessmentResults } from "../api/assessments";
import "../styles/dashboard.css";

function normalizeCatalog(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.assessments)) return payload.assessments;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

function assessmentKey(assessment) {
  return assessment.id || assessment.slug || assessment.assessment_type || assessment.type || assessment.name || assessment.title;
}

function assessmentTitle(assessment) {
  return assessment.name || assessment.title || assessment.assessment_name || "Simba Assessment";
}

function assessmentDescription(assessment) {
  return assessment.description || assessment.summary || assessment.short_description || "A guided Simba wa Ujamaa assessment to help shape your next step.";
}

export default function AssessmentCenter() {
  const [catalog, setCatalog] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startingKey, setStartingKey] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [catalogRes, resultsRes] = await Promise.all([getAssessmentCatalog(), getAssessmentResults()]);
        if (!mounted) return;
        setCatalog(normalizeCatalog(catalogRes));
        setResults(Array.isArray(resultsRes?.results) ? resultsRes.results : []);
      } catch (err) {
        if (mounted) setError(err.message || "Assessment Center is temporarily unavailable.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const latestResult = useMemo(() => results[0] || null, [results]);

  const startAssessment = async (assessment) => {
    const key = assessmentKey(assessment);
    setStartingKey(key);
    setError("");
    try {
      const response = await createAssessmentTransferToken(key);
      const target = `${response.start_url}?token=${encodeURIComponent(response.token)}`;
      window.location.assign(target);
    } catch (err) {
      setError(err.message || "We could not start this assessment yet.");
      setStartingKey(null);
    }
  };

  if (loading) return <div className="admin-loading">Loading Assessment Center...</div>;

  return (
    <main className="admin-dashboard member-launchpad command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header">
        <p className="member-kicker">Simba Assessment Center</p>
        <h1>Continue Your Journey</h1>
        <p className="subtitle">Choose a guided assessment, complete it securely, and return here for your Simba recommendations and STAR handling.</p>
        <div className="mission-status-strip"><span>Member-facing Simba experience</span><span>Single sign-on bridge active</span><span>Recommendations return here</span></div>
      </header>

      {error ? <section className="cosmic-section admin-error">⚠️ {error}</section> : null}

      {latestResult ? (
        <section className="cosmic-section member-hub-card member-hub-card--wide">
          <p className="section-kicker">Latest Assessment Result</p>
          <h2>{latestResult.assessment_name}</h2>
          <p><strong>Primary result:</strong> {typeof latestResult.primary_result === "string" ? latestResult.primary_result : JSON.stringify(latestResult.primary_result)}</p>
          <p><strong>Completed:</strong> {latestResult.completed_at ? new Date(latestResult.completed_at).toLocaleString() : "Recently"}</p>
          {latestResult.star_reward_eligible ? <p className="star-reward-label">STAR reward eligible · processed once through Simba participation.</p> : null}
          {latestResult.recommended_next_steps ? <pre className="data-note">{typeof latestResult.recommended_next_steps === "string" ? latestResult.recommended_next_steps : JSON.stringify(latestResult.recommended_next_steps, null, 2)}</pre> : null}
        </section>
      ) : null}

      <section className="cosmic-section member-hub-card member-hub-card--wide">
        <div className="section-heading-row">
          <div><p className="section-kicker">Available Assessments</p><h2>Start Assessment</h2></div>
          <Link to="/dashboard" className="member-action-btn member-action-btn--secondary">Back to Dashboard</Link>
        </div>
        {catalog.length === 0 ? <p>No assessments are open right now. Check back soon.</p> : (
          <div className="builder-dashboard-grid">
            {catalog.map((assessment) => {
              const key = assessmentKey(assessment);
              return (
                <article key={key}>
                  <h3>{assessmentTitle(assessment)}</h3>
                  <p>{assessmentDescription(assessment)}</p>
                  {assessment.estimated_minutes ? <p><strong>Time:</strong> {assessment.estimated_minutes} minutes</p> : null}
                  {assessment.star_reward ? <strong className="star-reward-label">STAR eligible</strong> : null}
                  <button type="button" className="member-action-btn" onClick={() => startAssessment(assessment)} disabled={startingKey === key}>
                    {startingKey === key ? "Opening..." : "Start Assessment"}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
