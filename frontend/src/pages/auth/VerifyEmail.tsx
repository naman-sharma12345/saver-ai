import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { authApi } from '../../api/auth';

export const VerifyEmail = () => {
  const [params] = useSearchParams();
  const [state, setState] = useState<'working' | 'ok' | 'bad'>('working');
  useEffect(() => {
    const t = params.get('token');
    if (!t) { setState('bad'); return; }
    authApi.verifyEmail(t).then(() => setState('ok')).catch(() => setState('bad'));
  }, [params]);
  return (
    <div className="text-center">
      <h1 className="text-[34px] font-semibold text-ink tracking-[-0.034em]">
        {state === 'working' ? 'Verifying...' : state === 'ok' ? 'Email verified' : 'Link not valid'}
      </h1>
      <p className="text-ink-2 mt-3">{state === 'ok' ? 'Thanks, you are all set.' : state === 'bad' ? 'Request a new verification email from your profile.' : ''}</p>
      <p className="mt-8"><Link to="/login" className="text-accent font-medium">Continue</Link></p>
    </div>
  );
};
