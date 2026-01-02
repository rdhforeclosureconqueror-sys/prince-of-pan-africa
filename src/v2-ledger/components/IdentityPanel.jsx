import React, { useEffect, useState } from 'react';
import { api } from '../../api/api';

export default function IdentityPanel() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    api('/auth/me').then((res) => {
      if (res?.ok && res.user) setUser(res.user);
    });
  }, []);

  if (!user) return null;

  const avatar = user.photo || '/assets/lion-logo.png';
  const displayId = user.googleId || user.email || 'Member';

  return (
    <div className="identity-panel">
      <img
        src={avatar}
        alt={`${user.displayName}'s profile photo`}
        className="identity-avatar"
      />
      <div>
        <h3 className="identity-name">{user.displayName}</h3>
        <p className="identity-id">ID: {displayId.slice(0, 10)}…</p>
        <span className="status-badge">ACTIVE MEMBER</span>
      </div>
    </div>
  );
}
