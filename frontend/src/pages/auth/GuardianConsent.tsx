import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { authApi } from '../../api/auth';
import { Button } from '../../components/ui/Button';

export const GuardianConsent = () => {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const [name, setName] = useState<string | null>(null);
  const [state, setState] = useState<'loading' | 'ask' | 'approved' | 'declined' | 'bad'>('loading');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) { setState('bad'); return; }
    authApi.guardianInfo(token).then((d) => { setName(d.name); setState('ask'); }).catch(() => setState('bad'));
  }, [token]);

  const decide = async (approve: boolean) => {
    setBusy(true);
    try { await authApi.guardianConsent(token, approve); setState(approve ? 'approved' : 'declined'); }
    catch { setState('bad'); }
    finally { setBusy(false); }
  };

  return (
    <div className="text-center">
      {state === 'loading' && <h1 className="text-[34px] font-semibold text-ink tracking-[-0.034em]">One moment...</h1>}
      {state === 'ask' && (<>
        <h1 className="text-[34px] leading-[1.1] font-semibold text-ink tracking-[-0.034em]">Approve {name}?</h1>
        <p className="text-ink-2 text-[17px] mt-3">{name} wants to use SaverAI to track their spending. They are under 18, so we need your approval before we store anything.</p>
        <p className="text-ink-3 text-[14px] mt-3">No ads. No tracking for marketing. If you decline, the account and its data are deleted.</p>
        <div className="mt-8 flex gap-3 justify-center">
          <Button onClick={() => decide(true)} isLoading={busy}>Approve</Button>
          <Button variant="secondary" onClick={() => decide(false)} disabled={busy}>Decline</Button>
        </div>
      </>)}
      {state === 'approved' && <><h1 className="text-[34px] font-semibold text-ink tracking-[-0.034em]">Approved</h1><p className="text-ink-2 mt-3">Thank you. {name} can sign in now.</p></>}
      {state === 'declined' && <><h1 className="text-[34px] font-semibold text-ink tracking-[-0.034em]">Declined</h1><p className="text-ink-2 mt-3">The account and its data were deleted.</p></>}
      {state === 'bad' && <><h1 className="text-[34px] font-semibold text-ink tracking-[-0.034em]">Link not valid</h1><p className="text-ink-2 mt-3">It may have expired or already been used. Ask them to sign up again or resend the request.</p></>}
      <p className="mt-8"><Link to="/login" className="text-accent font-medium">Back to sign in</Link></p>
    </div>
  );
};
