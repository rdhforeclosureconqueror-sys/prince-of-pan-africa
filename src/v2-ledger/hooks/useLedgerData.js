import { useEffect, useState, useCallback } from 'react';
import { getBalance } from '../api/ledgerV2Api';

export default function useLedgerData() {
  const [balance, setBalance] = useState({ stars: 0, bd: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refreshBalance = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getBalance();
      if (data?.ok) {
        setBalance({ stars: data.stars ?? 0, bd: data.bd ?? 0 });
        setError(null);
      } else throw new Error('Balance fetch failed');
    } catch (err) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshBalance();
  }, [refreshBalance]);

  return { balance, loading, error, refreshBalance };
}
