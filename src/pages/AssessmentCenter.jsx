import React, { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { createAssessmentTransferToken, getArchetypeCatalog, getAssessmentResult } from "../api/assessments";
import "../styles/dashboard.css";


const OFFICIAL_ASSESSMENTS = [
  ["Business Owner Assessment", "business-assessment", "business-owner"],
  ["Customer / Voice of Customer", "voice-of-customer", "customer-assessment", "voc"],
  ["Love Archetype Engine", "love-engine", "love-archetype"],
  ["Leadership Archetype Engine", "leadership-engine", "leadership-archetype"],
  ["Loyalty Archetype Engine", "loyalty-engine", "loyalty-archetype"],
  ["Youth Rite of Passage / Gates", "rite-of-passage", "gates"],
  ["K–6 Assessment MVP", "k6-assessment-mvp", "k-6", "k6"],
];

const ASSESSMENT_FAMILY_PREVIEWS = [
  {
    title: "Business Owner Assessment",
    shortTitle: "Business Owner",
    key: "business-owner-assessment",
    estimatedTime: "12–15 minutes",
    description: "Discover how you currently build, operate, and steward economic power.",
    discover: ["Your business owner archetype", "Your current operating strength", "The next constraint to remove"],
    whyItMatters: "A business is more than an idea. This assessment helps founders connect vision, systems, customers, and responsibility.",
    archetypeCollection: "business",
    archetypes: ["Creator", "Builder", "Architect", "Visionary", "Operator", "Strategist", "Steward", "Innovator"],
  },
  {
    title: "Voice of Customer Assessment",
    shortTitle: "Voice of Customer",
    key: "voice-of-customer",
    estimatedTime: "10–12 minutes",
    description: "Explore how you listen, interpret needs, and translate customer signals into better service.",
    discover: ["Your customer personality pattern", "How customers experience your offer", "What evidence should guide your next improvement"],
    whyItMatters: "Community-centered builders grow by listening before scaling. This assessment strengthens empathy, trust, and offer clarity.",
    archetypeCollection: "customer",
    archetypes: ["Listener", "Advocate", "Analyst", "Connector", "Problem Solver", "Experience Keeper"],
  },
  {
    title: "Love Archetype Engine",
    shortTitle: "Love",
    key: "love-archetype-engine",
    estimatedTime: "10–14 minutes",
    description: "Reflect on care, reciprocity, attachment, boundaries, and relational repair.",
    discover: ["Your relationship archetype", "Your care and connection strengths", "A growth practice for healthier bonds"],
    whyItMatters: "Liberation work is relational. Understanding how you love helps strengthen family, partnership, friendship, and community trust.",
    archetypeCollection: "love",
    archetypes: ["Nurturer", "Protector", "Healer", "Devotee", "Companion", "Truth Teller"],
  },
  {
    title: "Leadership Archetype Engine",
    shortTitle: "Leadership",
    key: "leadership-archetype-engine",
    estimatedTime: "12–15 minutes",
    description: "Preview how you lead, decide, delegate, organize, and serve under pressure.",
    discover: ["Your leadership archetype", "Your decision-making pattern", "Your next leadership growth edge"],
    whyItMatters: "Movements need disciplined leadership. This assessment helps members convert influence into service and accountability.",
    archetypeCollection: "leadership",
    archetypes: ["Architect", "Organizer", "Diplomat", "Strategist", "Teacher", "Guardian", "Catalyst", "Steward"],
  },
  {
    title: "Loyalty Archetype Engine",
    shortTitle: "Loyalty",
    key: "loyalty-archetype-engine",
    estimatedTime: "8–12 minutes",
    description: "Understand how commitment, trust, accountability, and belonging operate in your life.",
    discover: ["Your loyalty archetype", "How you build and protect trust", "Where boundaries or repair may be needed"],
    whyItMatters: "Loyalty without clarity can become strain. This assessment helps members practice commitment with wisdom and integrity.",
    archetypeCollection: "loyalty",
    archetypes: ["Guardian", "Ally", "Keeper", "Witness", "Protector", "Bridge Builder"],
  },
  {
    title: "Youth Rite of Passage",
    shortTitle: "Youth Rite of Passage",
    key: "youth-rite-of-passage",
    estimatedTime: "15–20 minutes",
    description: "Preview developmental pathways for identity, discipline, responsibility, and community readiness.",
    discover: ["A current developmental pathway", "Mentorship needs", "The next growth gate"],
    whyItMatters: "Young people need structure, affirmation, and responsibility. This assessment supports a guided path into maturity.",
    archetypeCollection: "youth",
    archetypes: ["Seed", "Pathfinder", "Apprentice", "Torchbearer", "Guardian-in-Training", "Community Builder"],
  },
  {
    title: "K–6 Learning Assessment",
    shortTitle: "K–6 Learning",
    key: "k-6-assessment-mvp",
    estimatedTime: "8–10 minutes with guardian support",
    description: "Preview learning profiles for younger members through curiosity, confidence, and support needs.",
    discover: ["A learning profile", "Confidence and curiosity signals", "Family or guardian next steps"],
    whyItMatters: "Early learning thrives when adults see the whole child. This assessment supports encouragement, patience, and targeted support.",
    archetypeCollection: "k-6",
    archetypes: ["Explorer", "Story Keeper", "Pattern Finder", "Creative Maker", "Question Asker", "Team Helper"],
  },
];

function flattenArchetypeCatalog(payload) {
  const catalog = payload?.catalog ?? payload;
  const items = Array.isArray(catalog) ? catalog : Array.isArray(catalog?.archetypes) ? catalog.archetypes : Array.isArray(catalog?.items) ? catalog.items : Array.isArray(catalog?.data) ? catalog.data : [];
  return items.filter(Boolean);
}

function archetypeMetadataFor(items, assessmentKey, collection, name) {
  const targetName = normalizeText(name);
  const targetCollection = normalizeText(collection);
  const targetAssessment = normalizeText(assessmentKey);
  return items.find((item) => {
    const itemName = normalizeText(item.name || item.title || item.archetype_name || item.slug);
    const itemCollection = normalizeText(item.collection || item.collection_slug || item.assessment_family || item.family || item.assessment_type || "");
    const itemAssessment = normalizeText(item.assessment_key || item.assessment_id || item.assessment_family || item.family || item.assessment_type || "");
    return itemName === targetName && (itemCollection.includes(targetCollection) || itemAssessment.includes(targetAssessment));
  });
}

function archetypeProfileUrl(item) {
  return item?.profile_url || item?.url || item?.canonical_url || item?.href || null;
}

function collectionUrlFor(items, assessmentKey, collection) {
  const targetCollection = normalizeText(collection);
  const targetAssessment = normalizeText(assessmentKey);
  const item = items.find((entry) => {
    const itemCollection = normalizeText(entry.collection || entry.collection_slug || entry.assessment_family || entry.family || entry.assessment_type || "");
    const itemAssessment = normalizeText(entry.assessment_key || entry.assessment_id || entry.assessment_family || entry.family || entry.assessment_type || "");
    return itemCollection.includes(targetCollection) || itemAssessment.includes(targetAssessment);
  });
  return item?.collection_url || item?.collectionUrl || null;
}

function normalizeText(value) {
  return String(value || "").toLowerCase().replace(/[–_\/]/g, "-").replace(/\s+/g, "-");
}

function isOfficialAssessment(assessment) {
  const raw = [assessment.id, assessment.slug, assessment.key, assessment.assessment_type, assessment.type, assessment.name, assessment.title, assessment.assessment_name].filter(Boolean).join(" ");
  const normalized = normalizeText(raw);
  return OFFICIAL_ASSESSMENTS.some((names) => names.some((name) => normalized.includes(normalizeText(name))));
}

function normalizeCatalog(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.assessments)) return payload.assessments;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.catalog)) return payload.catalog;
  return [];
}

function assessmentKey(assessment) {
  return assessment.id || assessment.slug || assessment.key || assessment.assessment_type || assessment.type || assessment.name || assessment.title;
}

function assessmentTitle(assessment) {
  return assessment.title || assessment.name || assessment.assessment_name || "Garvey Assessment";
}

function assessmentDescription(assessment) {
  return assessment.description || assessment.summary || assessment.short_description || "A guided assessment to help shape your next step.";
}

function assessmentTime(assessment) {
  const minutes = assessment.estimated_minutes || assessment.estimated_time_minutes || assessment.duration_minutes;
  if (minutes) return `${minutes} minutes`;
  return assessment.estimated_time || assessment.duration || "Time varies";
}

function assessmentCategory(assessment) {
  return assessment.category || assessment.domain || assessment.track || "Personal Development";
}

function completionFor(assessment, results) {
  const key = String(assessmentKey(assessment) || "").toLowerCase();
  return results.find((result) => {
    const candidates = [result.assessment_id, result.assessment_type, result.assessment_name, result.slug, result.id].filter(Boolean).map((item) => String(item).toLowerCase());
    return candidates.includes(key);
  });
}

function scoreFor(completion) {
  return completion?.overall_score ?? completion?.latest_score ?? null;
}

function statusFor(assessment, completion) {
  const raw = assessment.status || completion?.completion_status || (completion ? "completed" : "not_started");
  return String(raw).toLowerCase().replace(" ", "_");
}

function actionFor(status, completion) {
  if (status === "in_progress") return "Continue Assessment";
  if (status === "completed" && completion) return "View Results";
  if (status === "retake") return "Retake Assessment";
  return "Start Assessment";
}

function difficultyFor(assessment) {
  return assessment.difficulty || assessment.level || "Guided";
}

function recommendedNextFor(assessment, catalog, results) {
  const explicit = assessment.recommended_next_assessment || assessment.recommended_next || assessment.next_assessment;
  if (explicit) return typeof explicit === "string" ? explicit : assessmentTitle(explicit);
  const currentIndex = catalog.findIndex((item) => assessmentKey(item) === assessmentKey(assessment));
  const nextIncomplete = catalog.slice(currentIndex + 1).find((item) => !completionFor(item, results)) || catalog.find((item) => !completionFor(item, results) && assessmentKey(item) !== assessmentKey(assessment));
  return nextIncomplete ? assessmentTitle(nextIncomplete) : "Review your latest results";
}

function openGarveyWithToken(response) {
  const params = new URLSearchParams({ token: response.token, return_url: response.return_url || "https://simbawaujamaa.com/dashboard" });
  window.location.assign(`${response.start_url}?${params.toString()}`);
}

export default function AssessmentLandingPage() {
  const [archetypes, setArchetypes] = useState([]);
  const [startingKey, setStartingKey] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const response = await getArchetypeCatalog();
        if (mounted && response?.ok) setArchetypes(flattenArchetypeCatalog(response));
      } catch {
        if (mounted) setArchetypes([]);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const enterGarvey = async (assessmentKey = null) => {
    setStartingKey(assessmentKey || "center");
    setError("");
    try {
      openGarveyWithToken(await createAssessmentTransferToken(assessmentKey, assessmentKey ? "assessment" : "center"));
    } catch (err) {
      setError(err.message || "We could not open Garvey right now.");
      setStartingKey(null);
    }
  };

  return (
    <main className="admin-dashboard member-launchpad command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header">
        <p className="member-kicker">Simba wa Ujamaa Assessments</p>
        <h1>Official Assessment Landing Page</h1>
        <p className="subtitle">Begin with insight before you begin the assessment. Walk through the official assessment families, preview the archetypes you may discover, and then enter the operational Assessment Center when you are ready to choose your path.</p>
        <div className="mission-status-strip"><span>Native Simba journey</span><span>Powered by the Garvey Assessment Engine</span><span>Results sync to your dashboard</span></div>
        <div className="hero-cta-row">
          <button type="button" onClick={() => enterGarvey()} className="member-action-btn" disabled={startingKey === "center"}>{startingKey === "center" ? "Opening Garvey..." : "Enter Assessment Center"}</button>
          <Link to="/dashboard" className="member-action-btn member-action-btn--secondary">Back to Dashboard</Link>
        </div>
      </header>

      <section className="cosmic-section member-hub-card member-hub-card--wide">
        <p className="section-kicker">Educational entrance</p>
        <h2>Assessments are mirrors for action.</h2>
        <p>Each experience is designed to help members name strengths, understand patterns, and choose a next step with more clarity. Explore the previews below first; then move into the Official Assessment Center to launch the assessment, consent, complete questions, review results, and return to Simba.</p>
      </section>

      <section className="cosmic-section member-hub-card member-hub-card--wide">
        <div className="section-heading-row"><div><p className="section-kicker">Assessment previews</p><h2>Explore what you may discover</h2></div><button type="button" onClick={() => enterGarvey()} className="member-action-btn" disabled={startingKey === "center"}>{startingKey === "center" ? "Opening Garvey..." : "Take Assessment"}</button></div>
        {error ? <p className="admin-error">⚠️ {error}</p> : null}
        <div className="builder-dashboard-grid">
          {ASSESSMENT_FAMILY_PREVIEWS.map((assessment) => {
            const collectionUrl = collectionUrlFor(archetypes, assessment.key, assessment.archetypeCollection);
            return (
              <article key={assessment.key} className="member-hub-card">
                <p className="section-kicker">{assessment.estimatedTime}</p>
                <h3>{assessment.title}</h3>
                <p>{assessment.description}</p>
                <p><strong>What you will discover:</strong></p>
                <ul>{assessment.discover.map((item) => <li key={item}>{item}</li>)}</ul>
                <p><strong>Why it matters:</strong> {assessment.whyItMatters}</p>
                <p><strong>Archetype preview:</strong></p>
                <div className="command-chip-list" aria-label={`${assessment.shortTitle} archetype preview`}>
                  {assessment.archetypes.map((name) => {
                    const meta = archetypeMetadataFor(archetypes, assessment.key, assessment.archetypeCollection, name);
                    const url = archetypeProfileUrl(meta);
                    return url ? <a key={name} href={url}>{name}</a> : <span key={name}>{name}</span>;
                  })}
                </div>
                {collectionUrl ? <a href={collectionUrl} className="member-action-btn member-action-btn--secondary">View All {assessment.shortTitle} Archetypes</a> : <p className="data-note">Garvey archetype links are not published yet, so Simba is hiding links instead of guessing.</p>}
                <button type="button" onClick={() => enterGarvey(assessment.key)} className="member-action-btn" disabled={startingKey === assessment.key}>{startingKey === assessment.key ? "Opening Garvey..." : "Take Assessment"}</button>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}

export function AssessmentCenter() {
  const location = useLocation();
  const [error, setError] = useState("");

  useEffect(() => {
    const requestedAssessment = new URLSearchParams(location.search).get("assessment");
    (async () => {
      try {
        openGarveyWithToken(await createAssessmentTransferToken(requestedAssessment, requestedAssessment ? "assessment" : "center"));
      } catch (err) {
        setError(err.message || "We could not open Garvey right now.");
      }
    })();
  }, [location.search]);

  return (
    <main className="admin-dashboard member-launchpad command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header">
        <p className="member-kicker">Garvey Assessment Center</p>
        <h1>Opening Garvey’s official assessment center…</h1>
        <p className="subtitle">Simba is creating your secure transfer token and sending you directly to Garvey for consent, launch, results, and archetype pages.</p>
        {error ? <section className="cosmic-section admin-error">⚠️ {error}</section> : null}
        <Link to="/assessments" className="member-action-btn member-action-btn--secondary">Back to Simba Assessment Landing</Link>
      </header>
    </main>
  );
}

export function AssessmentResultPage() {
  const { resultId } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await getAssessmentResult(resultId);
        if (mounted) setResult(res?.result || null);
      } catch (err) {
        if (mounted) setError(err.message || "Result could not be loaded.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [resultId]);

  if (loading) return <div className="admin-loading">Loading result...</div>;

  return (
    <main className="admin-dashboard member-launchpad command-center-shell cosmic-readable-shell">
      <header className="mission-control member-hero dashboard-header">
        <p className="member-kicker">Saved Garvey Result</p>
        <h1>{result?.assessment_name || "Assessment Result"}</h1>
        <p className="subtitle">This result is stored in Simba from the signed Garvey callback.</p>
        <Link to="/dashboard" className="member-action-btn member-action-btn--secondary">Back to Simba Dashboard</Link>
      </header>
      {error ? <section className="cosmic-section admin-error">⚠️ {error}</section> : (
        <section className="cosmic-section member-hub-card member-hub-card--wide">
          <p><strong>Status:</strong> {result?.completion_status || "completed"}</p>
          <p><strong>Completed:</strong> {result?.completed_at ? new Date(result.completed_at).toLocaleString() : "Recently"}</p>
          <p><strong>Score:</strong> {result?.overall_score ?? "Not scored"}</p>
          <p><strong>Primary result:</strong> {typeof result?.primary_result === "string" ? result.primary_result : JSON.stringify(result?.primary_result || {})}</p>
          <p><strong>Recommended Next:</strong> {result?.recommended_next_assessment?.assessment_name || "Return to the Assessment Center for your next step."}</p>
          <h2>Strengths</h2>
          <ul>{(result?.strengths || []).map((item) => <li key={item}>{item}</li>)}</ul>
          <h2>Recommendations</h2>
          <pre className="data-note">{typeof result?.recommended_next_steps === "string" ? result.recommended_next_steps : JSON.stringify(result?.recommended_next_steps || result?.opportunities_for_growth || [], null, 2)}</pre>
          <Link to="/assessments/center" className="member-action-btn">Retake or Continue in Garvey</Link>
          <Link to="/dashboard" className="member-action-btn member-action-btn--secondary">Back to Simba Dashboard</Link>
        </section>
      )}
    </main>
  );
}
