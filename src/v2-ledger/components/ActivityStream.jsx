import React, { useEffect, useState } from 'react';

export default function ActivityStream() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    setItems([
      { id: 1, type: 'STAR', desc: 'Shared approved content', status: 'APPROVED' },
      { id: 2, type: 'BD', desc: 'Community reward granted', status: 'EARNED' },
    ]);
  }, []);

  return (
    <div className="activity-stream">
      <h3>Recent Activity</h3>
      <ul>
        {items.map(i => (
          <li key={i.id}>
            <span className={`tag ${i.type}`}>{i.type}</span>
            {i.desc} — <span className="status">{i.status}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
