import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getTrustBoard, updateTrustTask } from "../api/societyBuilder";
import "../styles/societyBuilder.css";

const COLUMNS = [
  ["backlog", "Backlog"],
  ["this_week", "This Week"],
  ["in_progress", "In Progress"],
  ["waiting", "Waiting"],
  ["completed", "Completed"],
];
const STATUSES = COLUMNS.map(([value]) => value);

export default function SocietyTrustBoardPage() {
  const { societyId } = useParams();
  const [board, setBoard] = useState(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  async function load() {
    const next = await getTrustBoard(societyId);
    setBoard(next);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message || "Unable to load Trust Board."));
  }, [societyId]);

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
  return <main className="society-builder-shell">
    <p className="society-kicker">Trust Board</p>
    <h1>{container?.title || "First 100 Days Container"}</h1>
    <p className="society-warning">Build the first trustworthy container. Mutual aid is organized responsibility.</p>
    <div className="society-actions"><Link className="society-btn secondary" to={`/societies/${societyId}`}>Back to Society Home</Link></div>
    {msg && <p className="society-success">{msg}</p>}{error && <p className="society-warning">{error}</p>}
    {container ? <section className="society-card">
      <h2>Mission Progress: {container.percent_complete}%</h2>
      <p>Current Day: {container.current_day} · Current Week: {container.current_week}</p>
      <p>Next Milestone: {container.active_milestone?.title || "Day 100 Report"}</p>
    </section> : <section className="society-card"><h2>No active container</h2><p>Start the First 100 Days Container from Society Home.</p></section>}
    <section className="society-board-grid">
      {COLUMNS.map(([key, label]) => <article className="society-card" key={key}>
        <h2>{label}</h2>
        {(board.columns?.[key] || []).map((task) => <div className="society-task-card" key={task.id}>
          <strong>{task.title}</strong>
          <p>{task.description}</p>
          <p>Owner: {task.owner_member_id || "Unassigned"}</p>
          <p>Due date: {task.due_date || "Not set"}</p>
          <p>Lane: {task.lane}</p>
          <p>Linked module: {task.linked_module || "None"}</p>
          <p>Handbook: {task.linked_handbook_chapter || task.linked_container_step || "None"}</p>
          {task.status === "waiting" && task.blocked_reason && <p className="society-warning">Blocked: {task.blocked_reason}</p>}
          <label>Status
            <select value={task.status} onChange={(e) => changeStatus(task, e.target.value)}>
              {STATUSES.map((status) => <option key={status} value={status}>{status.replace("_", " ")}</option>)}
            </select>
          </label>
        </div>)}
        {!(board.columns?.[key] || []).length && <p className="society-muted">No tasks in {label}.</p>}
      </article>)}
    </section>
  </main>;
}
