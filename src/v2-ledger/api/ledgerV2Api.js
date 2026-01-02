import { api } from '../../api/api';

// GET balance
export const getBalance = () => api('/ledger/balance');

// GET activity (with fallback)
export const getActivity = async () => {
  try {
    const data = await api('/ledger/activity');
    if (data?.ok && Array.isArray(data.items)) return data.items;
  } catch (err) {
    try {
      const [stars, bd] = await Promise.all([
        api('/ledger/star-transactions'),
        api('/ledger/bd-transactions'),
      ]);
      const merged = [
        ...(stars?.items || []),
        ...(bd?.items || []),
      ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      return merged;
    } catch {
      return [];
    }
  }
  return [];
};

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
