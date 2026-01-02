import React, { useEffect, useState } from 'react';
import { api } from '../../api/api';

export default function ActivityStream() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchActivity() {
      try {
        setLoading(true);
        const res = await api('/ledger/activity');

        if (!cancelled) {
          if (res?.ok && Array.isArray(res.items)) {
            setItems(res.items);
            setError(null);
          } else {
            throw new Error('Unexpected response format');
          }
        }
      } catch (e) {
        console.error('Error loading activity stream:', e);
        if (!cancelled) {
          setError('Unable to load recent activity');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchActivity();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="activity-stream">
      <h3>Recent Activity</h3>

      {loading && <p className="muted">Loading activity…</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !items.length && (
        <p className="muted">
          No activity yet — complete a share or review to earn your first STAR!
        </p>
      )}

      <ul>
        {items.map((tx) => (
          <li key={tx.id}>
            <span className={`tag ${tx.type}`}>{tx.type}</span>{' '}
            <strong>{tx.delta > 0 ? `+${tx.delta}` : tx.delta}</strong>{' '}
            {tx.desc} —{' '}
            <span className={`status ${tx.status.toLowerCase()}`}>
              {tx.status}
            </span>
            <span className="timestamp">
              {new Date(tx.created_at).toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
