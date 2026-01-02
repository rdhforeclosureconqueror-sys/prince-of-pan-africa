import { api } from '../../api/api';

// GET balance
export const getBalance = () => api('/ledger/balance');

// POST share
export const postShare = ({ share_platform, share_url, proof_url }) =>
  api('/ledger/share', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: { share_platform, share_url, proof_url },
  });

// POST review video
export const postReviewVideo = ({
  business_name,
  business_address,
  service_type,
  what_makes_special,
  video_url,
  checklist,
}) =>
  api('/ledger/review-video', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: {
      business_name,
      business_address,
      service_type,
      what_makes_special,
      video_url,
      checklist,
    },
  });
