import React, { useState } from 'react';
import { postReviewVideo } from '../api/ledgerV2Api';

export default function ReviewVideoModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({
    business_name: '',
    business_address: '',
    service_type: '',
    what_makes_special: '',
    video_url: '',
    checklist: {
      clear_business_shown: false,
      clear_service_explained: false,
      clear_location: false,
      audio_clear: false,
      respectful: false,
    },
  });
  const [loading, setLoading] = useState(false);

  const toggleCheck = key =>
    setForm(f => ({ ...f, checklist: { ...f.checklist, [key]: !f.checklist[key] } }));

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    await postReviewVideo(form);
    setLoading(false);
    onSuccess();
    onClose();
  }

  return (
    <div className="modal-overlay">
      <form className="modal" onSubmit={handleSubmit}>
        <h2>Submit Review Video</h2>
        <input required placeholder="Business Name" value={form.business_name} onChange={e => setForm({ ...form, business_name: e.target.value })}/>
        <input placeholder="Address" value={form.business_address} onChange={e => setForm({ ...form, business_address: e.target.value })}/>
        <input placeholder="Service Type" value={form.service_type} onChange={e => setForm({ ...form, service_type: e.target.value })}/>
        <input placeholder="What Makes It Special?" value={form.what_makes_special} onChange={e => setForm({ ...form, what_makes_special: e.target.value })}/>
        <input required placeholder="Video URL" value={form.video_url} onChange={e => setForm({ ...form, video_url: e.target.value })}/>
        <div className="checklist">
          {Object.keys(form.checklist).map((key) => (
            <label key={key}>
              <input type="checkbox" checked={form.checklist[key]} onChange={() => toggleCheck(key)} /> {key.replaceAll('_', ' ')}
            </label>
          ))}
        </div>
        <div className="modal-actions">
          <button type="button" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={loading}>{loading ? 'Submitting…' : 'Submit'}</button>
        </div>
      </form>
    </div>
  );
}
