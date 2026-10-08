import { useQuery } from '@tanstack/react-query';
import { billingApi } from '../api/billing';
import { useAuth } from '../context/AuthContext';

export const useBillingStatus = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({ queryKey: ['billing', 'status'], queryFn: billingApi.status, enabled: isAuthenticated, staleTime: 60_000 });
};

/** hasFeature stays true while loading so locked UI never flashes for paying users. */
export const useEntitlement = () => {
  const { data, isLoading } = useBillingStatus();
  const ent = data?.entitlement;
  return {
    isLoading,
    status: data,
    entitlement: ent,
    hasFeature: (f: string) => (isLoading || !ent ? true : ent.features.includes(f)),
  };
};
