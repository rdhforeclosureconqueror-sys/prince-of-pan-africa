import React, { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getMutualAidRequest, saveMutualAidDraft, submitMutualAidRequest } from "../api/mutualAidRequests";
import "../styles/mutualAid.css";

const initialForm = {
  category: "housing",
  urgency: "standard",
  requested_amount: 100,
  explanation: "",
  preferred_support_method: "community_follow_up",
  policy_consent: false,
};

export function MutualAidRequestFormPage() {
  const [form, setForm] = useState(initialForm);
  const [saved, setSaved] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const update = (key) => (event) => setForm({ ...form, [key]: key === "policy_consent" ? event.target.checked : event.target.value });

  async function saveDraft(event) {
    event.preventDefault();
    setError("");
    try {
      const response = await saveMutualAidDraft({ ...form, requested_amount: Number(form.requested_amount) });
      setSaved(response.request);
    } catch (err) {
      setError(err.message || "Unable to save draft");
    }
  }

  async function submitDraft() {
    if (!saved?.id) return;
    const response = await submitMutualAidRequest(saved.id);
    navigate(`/mutual-aid/requests/${response.request.id}`);
  }

  return (
    <main className="mutual-aid-page cosmic-readable-shell">
      <p className="eyebrow">Member Mutual Aid</p>
      <h1>Request intake</h1>
      <p>This intake records a member request only. It does not approve aid, create payments, payouts, wallets, reimbursements, or disbursements.</p>
      <form className="mutual-aid-card" onSubmit={saveDraft}>
        <label>Category<select value={form.category} onChange={update("category")}><option value="housing">Housing</option><option value="utilities">Utilities</option><option value="food">Food</option><option value="transportation">Transportation</option><option value="medical">Medical</option><option value="childcare">Childcare</option><option value="emergency">Emergency</option><option value="other">Other</option></select></label>
        <label>Urgency<select value={form.urgency} onChange={update("urgency")}><option value="standard">Standard</option><option value="urgent">Urgent</option><option value="emergency">Emergency</option></select></label>
        <label>Requested amount (USD)<input type="number" min="1" value={form.requested_amount} onChange={update("requested_amount")} /></label>
        <label>Preferred support method<select value={form.preferred_support_method} onChange={update("preferred_support_method")}><option value="community_follow_up">Community follow-up</option><option value="resource_referral">Resource referral</option><option value="direct_vendor">Direct vendor coordination</option><option value="member_follow_up">Member follow-up</option><option value="other">Other</option></select></label>
        <label>Explanation<textarea required minLength="20" value={form.explanation} onChange={update("explanation")} /></label>
        <label className="mutual-aid-consent"><input type="checkbox" checked={form.policy_consent} onChange={update("policy_consent")} /> I understand this is intake only and does not guarantee approval or payment.</label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">Save draft</button>
        <button type="button" disabled={!saved?.id} onClick={submitDraft}>Submit request</button>
      </form>
      {saved ? <p>Draft saved. <Link to={`/mutual-aid/requests/${saved.id}`}>View status</Link></p> : null}
    </main>
  );
}

export function MutualAidRequestStatusPage() {
  const { requestId } = useParams();
  const [state, setState] = React.useState({ loading: true, request: null, error: "" });
  React.useEffect(() => { getMutualAidRequest(requestId).then((r) => setState({ loading: false, request: r.request, error: "" })).catch((e) => setState({ loading: false, request: null, error: e.message })); }, [requestId]);
  if (state.loading) return <main className="mutual-aid-page cosmic-readable-shell">Loading request status...</main>;
  if (state.error) return <main className="mutual-aid-page cosmic-readable-shell"><h1>Request unavailable</h1><p>{state.error}</p></main>;
  const request = state.request;
  return <main className="mutual-aid-page cosmic-readable-shell"><p className="eyebrow">Member Mutual Aid</p><h1>Request status</h1><section className="mutual-aid-card"><p><strong>Status:</strong> {request.status}</p><p><strong>Category:</strong> {request.category}</p><p><strong>Urgency:</strong> {request.urgency}</p><p><strong>Requested amount:</strong> ${request.requested_amount}</p><p><strong>Preferred support:</strong> {request.preferred_support_method}</p><p>{request.explanation}</p></section></main>;
}
