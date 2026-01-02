import React from 'react';

export default function BalanceCore({ balance, loading }) {
  const bd = Number(balance?.bd ?? 0);
  const stars = Number(balance?.stars ?? 0);

  return (
    <div className="balance-core">
      <div className="balance-block">
        <h1 aria-live="polite">⭐ {loading ? '…' : stars}</h1>
        <p>Participation Credits</p>
      </div>
      <div className="balance-block">
        <h1>💰 {loading ? '…' : bd.toLocaleString()}</h1>
        <p>Community Currency (Black Dollars)</p>
      </div>
    </div>
  );
}
