import React, { useEffect, useState } from "react";
import { approveChapter, declineChapter, getChapterApplications, requestChapterChanges } from "../api/societyBuilder";
import "../styles/societyBuilder.css";

const LABELS = { pending_review: "Pending Review", approved: "Approved", changes_requested: "Changes Requested", declined: "Declined", local_society: "Local Society", independent_society: "Independent Society", main_hub: "Main Hub", state_hub: "State Hub", city_hub: "City Hub" };
const humanize = (value) => LABELS[value] || value || "Not set";

export default function SocietyChapterAdminPage() {
  const [data, setData] = useState({ applications: [] });
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  function load() { return getChapterApplications().then(setData).catch((e) => setError(e.message)); }
  useEffect(() => { load(); }, []);
  async function run(fn, text) { setError(""); setMsg(""); try { await fn(); setMsg(text); await load(); } catch (e) { setError(e.message); } }
  return <main className="society-builder-shell"><p className="society-kicker">Chapter Reviewer</p><h1>Chapter Applications</h1>{msg && <p className="society-success">{msg}</p>}{error && <p className="society-warning">{error}</p>}<section className="society-grid">{data.applications?.map((s) => <article className="society-card" key={s.id}><h2>{s.name}</h2><p>{humanize(s.lifecycle_stage)} · {humanize(s.chapter_level)}</p><p>{humanize(s.affiliation_status)}</p><button className="society-btn" onClick={() => run(() => approveChapter(s.id), `${s.name} approved.`)}>Approve</button><button className="society-btn secondary" onClick={() => run(() => requestChapterChanges(s.id), `Changes requested for ${s.name}.`)}>Request Changes</button><button className="society-btn secondary" onClick={() => run(() => declineChapter(s.id), `${s.name} declined.`)}>Decline</button></article>)}{!data.applications?.length ? <article className="society-card"><h2>No pending chapter applications</h2><p>Approved, declined, and changes-requested societies are removed from this pending queue.</p></article> : null}</section></main>;
}
