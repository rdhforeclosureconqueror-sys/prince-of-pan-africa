import React, { useState } from 'react';
import { postShare } from '../api/ledgerV2Api';

export default function EarnStarModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ share_platform: '', share_url: '', proof_url: '' });
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    await postShare(form);
    setLoading(false);
    onSuccess();
    onClose();
  }

  return (
    <div className="modal-overlay">
      <form className="modal" onSubmit={handleSubmit}>
        <h2>Log a Share</h2>
        <select required value={form.share_platform} onChange={e => setForm({ ...form, share_platform: e.target.value })}>
          <option value="">Select Platform</option>
          <option>Instagram</option>
          <option>TikTok</option>
          <option>Twitter</option>
        </select>
        <input placeholder="Share URL (optional)" value={form.share_url} onChange={e => setForm({ ...form, share_url: e.target.value })}/>
        <input placeholder="Proof URL (optional)" value={form.proof_url} onChange={e => setForm({ ...form, proof_url: e.target.value })}/>
        <div className="modal-actions">
          <button type="button" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={loading}>{loading ? 'Submitting…' : 'Submit'}</button>
        </div>
      </form>
    </div>
  );
}
