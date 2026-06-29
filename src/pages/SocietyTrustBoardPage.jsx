import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getTrustBoard, getTrustTaskReaderReference, updateTrustTask } from "../api/societyBuilder";
import { CONTAINER_GUIDE_SOURCE_TITLE, containerGuideEntries, findContainerGuideEntryForTask } from "../data/societyContainerGuide";
import { findFirst100FullChapter, first100ChapterIdFromLabel } from "../data/first100DaysFullChapters";
import "../styles/societyBuilder.css";

const COLUMNS = [
  ["backlog", "📥 Backlog", "Work we know we need to do."],
  ["this_week", "📅 This Week", "Work members committed to now."],
  ["in_progress", "⚡ In Progress", "Work currently moving."],
  ["waiting", "⏳ Waiting", "Blocked, paused, or waiting on someone."],
  ["completed", "✅ Completed", "Institutional memory: what the society has actually done."],
];
const STATUSES = COLUMNS.map(([value]) => value);
const STATUS_LABELS = Object.fromEntries(COLUMNS.map(([value, label]) => [value, label.replace(/^\S+\s/, "")]));
const LANE_META = {
  people: ["👥", "People", "Founding members, roles, care teams"],
  systems: ["⚙️", "Systems", "Purpose, covenant, rules, treasury, records"],
  projects: ["🛠️", "Projects", "First action, assignments, execution"],
  community_impact: ["🌍", "Community Impact", "Needs, skills, service, results, reports"],
};
const EMPTY_STATES = {
  backlog: "Nothing waiting. The foundation is clear.",
  this_week: "Choose a few tasks to carry this week.",
  in_progress: "No active work yet. Move one task here when someone starts.",
  waiting: "Nothing blocked. Keep the rhythm moving.",
  completed: "No completed tasks yet. Every finished task becomes part of the society’s memory.",
};
const MILESTONE_ICONS = ["🧭", "👥", "🧱", "⚙️", "🛠️", "📜"];

export default function SocietyTrustBoardPage() {
  const { societyId } = useParams();
  const [board, setBoard] = useState(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [showGuide, setShowGuide] = useState(true);
  const [activeGuideId, setActiveGuideId] = useState("chapter-1");
  const navigate = useNavigate();

  async function load() {
    const next = await getTrustBoard(societyId);
    setBoard(next);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message || "Unable to load Trust Board."));
  }, [societyId]);

  async function openReading(task, onMissingChapter) {
    setError("");
    setMsg("");
    const label = task.source_chapter_label || task.linked_handbook_chapter || task.linked_container_step || "";
    const repoChapter = findFirst100FullChapter(label);
    if (repoChapter) {
      navigate(`/societies/${societyId}/containers/first-100-days/chapter/${repoChapter.id}`);
      return;
    }
    try {
      const res = await getTrustTaskReaderReference(societyId, task.id);
      const reference = res.reference || {};
      if (reference.connected && reference.reader_path) {
        navigate(reference.reader_path);
      } else if (reference.reader_path && reference.reader_path !== "/study") {
        navigate(reference.reader_path);
      } else {
        onMissingChapter?.("Full chapter text is not connected yet.");
      }
    } catch (e) {
      setError(e.message || "Unable to open the handbook reference.");
    }
  }

  function openGuideForTask(task) {
    const entry = findContainerGuideEntryForTask(task);
    if (entry) {
      setActiveGuideId(entry.id);
      setShowGuide(true);
      document.getElementById("container-guide")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  async function changeStatus(task, status) {
    setError("");
    setMsg("");
    try {
      await updateTrustTask(societyId, task.id, { status });
      await load();
      setMsg(`Updated ${task.title}.`);
    } catch (e) {
      setError(e.message || "Unable to update task status.");
    }
  }

  if (!board) return <main className="society-builder-shell"><p>Loading Trust Board...</p>{error && <p className="society-warning">{error}</p>}</main>;
  const container = board.container;
  const allTasks = COLUMNS.flatMap(([key]) => board.columns?.[key] || []);
  const activeGuideEntry = containerGuideEntries.find((entry) => entry.id === activeGuideId) || containerGuideEntries[0];
  const guideConnectedTasks = allTasks.filter((task) => activeGuideEntry?.connectedTasks?.some((title) => task.title === title || task.linked_handbook_chapter === activeGuideEntry.chapterLabel));

  const milestoneCounts = allTasks.reduce((acc, task) => {
    if (!task.milestone_id) return acc;
    acc[task.milestone_id] = acc[task.milestone_id] || { total: 0, completed: 0 };
    acc[task.milestone_id].total += 1;
    if (task.status === "completed") acc[task.milestone_id].completed += 1;
    return acc;
  }, {});

  return <main className="society-builder-shell trust-command-shell">
    <div className="society-actions"><Link className="society-btn secondary" to={`/societies/${societyId}`}>Back to Society Home</Link></div>
    {msg && <p className="society-success">{msg}</p>}{error && <p className="society-warning">{error}</p>}
    {container ? <>
      <section className="trust-hero society-card">
        <div className="trust-hero-copy">
          <p className="society-kicker">Trust Board</p>
          <h1>🚀 First 100 Days Trust Board</h1>
          <p className="trust-lede">Build the first trustworthy container before wealth arrives.</p>
          <p className="society-muted">The handbook teaches the process. The Trust Board turns it into weekly work.</p>
          <div className="trust-progress-row"><strong>Mission Progress: {container.percent_complete}%</strong><span>Day {container.current_day} of 100 · Week {container.current_week}</span></div>
          <div className="trust-progress-bar" aria-label={`Mission Progress ${container.percent_complete}%`}><span style={{ width: `${container.percent_complete || 0}%` }} /></div>
          <p className="trust-next">Next Milestone: <strong>{container.active_milestone?.title || "Generate Day 100 Report"}</strong></p>
        </div>
        <div className="trust-metric-grid">
          {Object.entries(LANE_META).map(([key, [icon, label, text]]) => <article className="trust-metric-card" key={key}><span>{icon}</span><strong>{label}</strong><p>{text}</p></article>)}
        </div>
      </section>

      <section className="trust-guide society-card" id="container-guide">
        <div className="trust-section-heading"><div><p className="society-kicker">Container Guide</p><h2>Operational breakdown of the handbook</h2><p className="society-muted">This guide summarizes the chapter for action. Use Read Full Chapter to study the complete teaching.</p><p className="society-muted">Source: {CONTAINER_GUIDE_SOURCE_TITLE}</p></div><button className="society-btn secondary" onClick={() => setShowGuide((value) => !value)}>{showGuide ? "Hide Guide" : "Show Guide"}</button></div>
        {showGuide && activeGuideEntry && <div className="trust-guide-body trust-container-guide">
          <div className="trust-guide-picker" role="list" aria-label="Container Guide chapters">{containerGuideEntries.map((entry) => <button type="button" role="listitem" key={entry.id} className={entry.id === activeGuideEntry.id ? "is-active" : ""} onClick={() => setActiveGuideId(entry.id)}>Ch. {entry.chapterNumber}</button>)}</div>
          <article className="trust-guide-entry">
            <p className="society-kicker">{activeGuideEntry.chapterLabel}</p><h3>{activeGuideEntry.title}</h3><p className="trust-core-question"><strong>Core question:</strong> {activeGuideEntry.coreQuestion}</p>{findFirst100FullChapter(activeGuideEntry.chapterLabel) && <Link className="society-btn trust-guide-reader-btn" to={`/societies/${societyId}/containers/first-100-days/chapter/${first100ChapterIdFromLabel(activeGuideEntry.chapterLabel)}`}>📖 Read Full Chapter</Link>}
            <div className="trust-guide-two"><GuideBlock title="What it means" items={[activeGuideEntry.meaning]} /><GuideBlock title="Why it matters" items={[activeGuideEntry.whyItMatters]} /></div>
            <div className="trust-guide-three"><GuideBlock title="Discuss" items={activeGuideEntry.discuss} /><GuideBlock title="Build" items={activeGuideEntry.build} /><GuideBlock title="Record in Simba" items={activeGuideEntry.recordInSimba} /></div>
            <div className="trust-guide-tasks"><h4>Connected Trust Board tasks</h4>{guideConnectedTasks.length ? <ul>{guideConnectedTasks.map((task) => <li key={task.id}><button type="button" onClick={() => setActiveGuideId(findContainerGuideEntryForTask(task)?.id || activeGuideEntry.id)}>{task.title}</button><span>{task.status?.replace("_", " ")}</span></li>)}</ul> : <p className="society-muted">No active Trust Board task is directly tied to this chapter yet.</p>}</div>
          </article>
        </div>}
      </section>

      <section className="trust-roadmap society-card"><p className="society-kicker">Milestone Roadmap</p><h2>From trust to institution</h2><div className="trust-roadmap-track">{(container.milestones || []).map((m, index) => { const counts = milestoneCounts[m.id] || { total: 0, completed: 0 }; const pct = counts.total ? Math.round((counts.completed / counts.total) * 100) : 0; return <article className={`trust-milestone ${m.id === container.active_milestone_id ? "is-current" : ""}`} key={m.id}><span className="trust-milestone-icon">{MILESTONE_ICONS[index] || "◆"}</span><strong>{m.title}</strong><small>{m.status?.replace("_", " ") || "not started"}</small><p>{counts.completed}/{counts.total} tasks · {pct}%</p></article>; })}</div></section>

      <section className="society-board-grid trust-board-grid">
        {COLUMNS.map(([key, label, description]) => { const tasks = board.columns?.[key] || []; return <article className={`society-card trust-column trust-column-${key}`} key={key}>
          <div className="trust-column-head"><div><h2>{label}</h2><p>{description}</p>{key === "completed" && <p className="trust-memory">Completed work becomes society memory.</p>}</div><span className="trust-count">{tasks.length}</span></div>
          {tasks.map((task) => <TaskCard key={task.id} task={task} onStatusChange={changeStatus} onOpenReading={openReading} onOpenGuide={openGuideForTask} />)}
          {!tasks.length && <p className="society-muted trust-empty">{EMPTY_STATES[key]}</p>}
        </article>; })}
      </section>
    </> : <section className="society-card trust-empty-container"><h1>🚀 Start the First 100 Days Container</h1><p>This will turn the handbook into milestones, tasks, and weekly work for your society.</p><p>Start the container from Society Home.</p></section>}
  </main>;
}

function GuideBlock({ title, items }) {
  return <div className="trust-guide-block"><h4>{title}</h4><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></div>;
}

function TaskCard({ task, onStatusChange, onOpenReading, onOpenGuide }) {
  const lane = LANE_META[task.lane] || ["◆", task.lane || "Lane", ""];
  return <div className={`society-task-card trust-task-card ${task.status === "completed" ? "is-completed" : ""}`}>
    <div className="trust-card-badges"><span className="trust-badge">{task.status === "completed" ? "✅ Completed" : STATUS_LABELS[task.status] || task.status}</span><span className="trust-badge lane">{lane[0]} {lane[1]}</span></div>
    <h3>{task.title}</h3>
    <p>{task.description}</p>
    {task.status === "completed" && <p className="trust-complete-note">✅ Completed — This strengthens the container.</p>}
    <div className="trust-task-meta"><span>🙋 Owner: {task.owner_member_id || "Unassigned"}</span><span>🗓️ Due: {task.due_date || "Not set"}</span><span>🔗 Module: {task.linked_module || "None"}</span><RelatedReading task={task} onOpenReading={onOpenReading} onOpenGuide={onOpenGuide} />{task.status === "waiting" && task.blocked_reason && <span className="trust-blocked">🚧 Blocked: {task.blocked_reason}</span>}</div>
    <label>Status<select value={task.status} onChange={(e) => onStatusChange(task, e.target.value)}>{STATUSES.map((status) => <option key={status} value={status}>{status.replace("_", " ")}</option>)}</select></label>
  </div>;
}


function RelatedReading({ task, onOpenReading, onOpenGuide }) {
  const [notice, setNotice] = useState("");
  const label = task.source_chapter_label || task.linked_handbook_chapter || task.linked_container_step || "";
  if (!label) return <span>📖 Chapter: None</span>;
  const hasSource = task.source_book_slug || task.source_book_id || task.source_reader_path || task.source_chapter_label || task.linked_handbook_chapter;
  return <span className="trust-related-reading">
    <strong>📖 Chapter</strong>
    <em>{label}</em>
    {hasSource ? <button type="button" className="trust-reading-link" onClick={() => onOpenReading(task, setNotice)}>Read Full Chapter</button> : <small>Full chapter text is not connected yet.</small>}
    <strong>🧭 Guide</strong>
    <button type="button" className="trust-reading-link secondary" onClick={() => onOpenGuide(task)}>Open Task Guide</button>
    {notice && <small className="trust-inline-notice">{notice}</small>}
  </span>;
}
