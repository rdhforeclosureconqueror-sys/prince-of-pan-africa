import React from "react";
import { Link, useParams } from "react-router-dom";
import {
  addMutualAidRecommendation,
  assignMutualAidReviewer,
  discloseMutualAidConflict,
  getMutualAidAdminRequest,
  getMutualAidAdminRequests,
  requestMutualAidMoreInfo,
} from "../api/mutualAidRequests";
import { formatMutualAidCurrency } from "../mutualAidFundProgress";

function StatusBadge({ status }) {
  return <span className="library-pill library-pill--green">{status || "unknown"}</span>;
}

export function MutualAidAdminReviewQueuePage() {
  const [state, setState] = React.useState({ loading: true, requests: [], error: "" });
  React.useEffect(() => {
    getMutualAidAdminRequests()
      .then((data) => setState({ loading: false, requests: data.requests || [], error: "" }))
      .catch((error) => setState({ loading: false, requests: [], error: error.message }));
  }, []);

  return (
    <main className="library-shell">
      <section className="library-inner cosmic-readable-shell">
        <h1>Mutual Aid review queue</h1>
        <p>Admin-only queue for submitted requests. This workflow records assignments, reviewer notes, recommendations, conflict disclosures, more-information requests, status history, and audit events only.</p>
        {state.loading ? <p>Loading review queue...</p> : null}
        {state.error ? <p className="form-error">{state.error}</p> : null}
        <div className="library-grid">
          {state.requests.map((request) => (
            <article className="library-card" key={request.id}>
              <h2>Request #{request.id}</h2>
              <p><StatusBadge status={request.status} /> {request.category} · {request.urgency}</p>
              <p>{formatMutualAidCurrency(request.requested_amount)} requested</p>
              <Link className="library-pill" to={`/admin/mutual-aid/review/${request.id}`}>Review details</Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export function MutualAidAdminRequestDetailPage() {
  const { requestId } = useParams();
  const [state, setState] = React.useState({ loading: true, detail: null, error: "" });
  const [reviewerUserId, setReviewerUserId] = React.useState("");
  const [recommendation, setRecommendation] = React.useState("needs_committee_review");
  const [notes, setNotes] = React.useState("");
  const [moreInfo, setMoreInfo] = React.useState("");
  const [conflict, setConflict] = React.useState("");
  const [message, setMessage] = React.useState("");

  const refresh = React.useCallback(() => {
    return getMutualAidAdminRequest(requestId)
      .then((data) => setState({ loading: false, detail: data, error: "" }))
      .catch((error) => setState({ loading: false, detail: null, error: error.message }));
  }, [requestId]);

  React.useEffect(() => { refresh(); }, [refresh]);

  async function runAction(action, success) {
    setMessage("");
    try {
      await action();
      setMessage(success);
      await refresh();
    } catch (error) {
      setMessage(error.message);
    }
  }

  const detail = state.detail;
  const request = detail?.request;

  return (
    <main className="library-shell">
      <section className="library-inner cosmic-readable-shell">
        <Link to="/admin/mutual-aid/review">← Back to queue</Link>
        <h1>Mutual Aid request review</h1>
        {state.loading ? <p>Loading request...</p> : null}
        {state.error ? <p className="form-error">{state.error}</p> : null}
        {message ? <p>{message}</p> : null}
        {request ? (
          <>
            <article className="library-card">
              <h2>Request #{request.id}</h2>
              <p><StatusBadge status={request.status} /> {request.category} · {request.urgency}</p>
              <p>{formatMutualAidCurrency(request.requested_amount)} requested via {request.preferred_support_method}</p>
              <p>{request.explanation}</p>
              <p>Requester: {detail.requester?.email || "private member"}</p>
            </article>

            <section className="library-card">
              <h2>Assign reviewer</h2>
              <input value={reviewerUserId} onChange={(event) => setReviewerUserId(event.target.value)} placeholder="Reviewer user ID" />
              <button type="button" onClick={() => runAction(() => assignMutualAidReviewer(request.id, reviewerUserId), "Reviewer assigned.")}>Assign reviewer</button>
            </section>

            <section className="library-card">
              <h2>Reviewer recommendation and notes</h2>
              <select value={recommendation} onChange={(event) => setRecommendation(event.target.value)}>
                <option value="needs_committee_review">Needs committee review</option>
                <option value="support">Support</option>
                <option value="do_not_support">Do not support</option>
              </select>
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Reviewer notes" />
              <button type="button" onClick={() => runAction(() => addMutualAidRecommendation(request.id, { recommendation, notes }), "Recommendation recorded.")}>Record recommendation</button>
            </section>

            <section className="library-card">
              <h2>Request more information</h2>
              <textarea value={moreInfo} onChange={(event) => setMoreInfo(event.target.value)} placeholder="Information needed from requester" />
              <button type="button" onClick={() => runAction(() => requestMutualAidMoreInfo(request.id, moreInfo), "More information requested.")}>Request more info</button>
            </section>

            <section className="library-card">
              <h2>Conflict disclosure</h2>
              <textarea value={conflict} onChange={(event) => setConflict(event.target.value)} placeholder="Disclose any conflict of interest" />
              <button type="button" onClick={() => runAction(() => discloseMutualAidConflict(request.id, conflict), "Conflict disclosed.")}>Disclose conflict</button>
            </section>

            <section className="library-card"><h2>Reviews</h2>{detail.reviews?.map((r) => <p key={r.id}>#{r.id}: {r.status} by user {r.reviewer_user_id} — {r.notes}</p>)}</section>
            <section className="library-card"><h2>Status history</h2>{detail.status_history?.map((h) => <p key={h.id}>{h.from_status || "none"} → {h.to_status}: {h.reason}</p>)}</section>
            <section className="library-card"><h2>Conflicts</h2>{detail.conflicts?.map((c) => <p key={c.id}>{c.status}: {c.disclosure}</p>)}</section>
          </>
        ) : null}
      </section>
    </main>
  );
}
