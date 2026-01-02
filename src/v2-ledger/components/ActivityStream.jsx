import React, { useEffect, useState } from 'react';
import { getActivity } from '../api/ledgerV2Api';

export default function ActivityStream() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await getActivity();
        setItems(res || []);
      } catch (e) {
        setError('Unable to load activity');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="activity-stream">
      <h3>Recent Activity</h3>

      {loading && <p className="muted">Loading activity…</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !items.length && (
        <p className="muted">No activity yet — complete a share or review to earn your first STAR!</p>
      )}

      <ul>
        {items.map((i) => (
          <li key={i.id || i.created_at}>
            <span className={`tag ${i.type}`}>{i.type}</span>
            {i.desc || i.description || 'Transaction'} — 
            <span className="status">{i.status || 'PENDING'}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
