import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { expensesApi } from '../api/expenses';
import { analyticsApi } from '../api/analytics';
import { storesApi, recommendationsApi, budgetsApi, profileApi, parentApi } from '../api/services';
import toast from 'react-hot-toast';

// --- Expenses Hooks ---
export const useExpenses = (params?: any) => {
  return useQuery({
    queryKey: ['expenses', params],
    queryFn: () => expensesApi.getAll(params),
  });
};

export const useAnomalies = () => {
  return useQuery({
    queryKey: ['anomalies'],
    queryFn: () => expensesApi.getAnomalies(),
  });
};

export const useCreateExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: expensesApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      queryClient.invalidateQueries({ queryKey: ['healthScore'] });
      if (data.categorization?.method === 'ml') {
        toast.success(`Expense saved and AI-categorized as ${data.expense.category}`);
      } else {
        toast.success('Expense saved successfully');
      }
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error || 'Failed to create expense');
    }
  });
};

export const useDeleteExpense = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: expensesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      queryClient.invalidateQueries({ queryKey: ['healthScore'] });
      toast.success('Expense deleted');
    },
  });
};

// --- Analytics Hooks ---
export const useSpendingByCategory = (month?: string) => {
  return useQuery({
    queryKey: ['analytics', 'category', month],
    queryFn: () => analyticsApi.getSpendingByCategory(month),
  });
};

export const useSpendingOverTime = (months: number = 6) => {
  return useQuery({
    queryKey: ['analytics', 'overTime', months],
    queryFn: () => analyticsApi.getSpendingOverTime(months),
  });
};

export const useHealthScore = () => {
  return useQuery({
    queryKey: ['healthScore'],
    queryFn: () => analyticsApi.getHealthScore(),
  });
};

export const useNextMonthPrediction = () => {
  return useQuery({
    queryKey: ['analytics', 'prediction'],
    queryFn: () => analyticsApi.getNextMonthPrediction(),
  });
};

export const useBudgetVsActual = (month: string) => {
  return useQuery({
    queryKey: ['analytics', 'budgetVsActual', month],
    queryFn: () => analyticsApi.getBudgetVsActual(month),
    enabled: !!month,
  });
};

// --- Stores & Recommendations Hooks ---
export const useNearbyStores = (params: { lat: number; lng: number; radius?: number; category?: string }, enabled = false) => {
  return useQuery({
    queryKey: ['stores', 'nearby', params],
    queryFn: () => storesApi.getNearby(params),
    enabled,
  });
};

export const useCheaperAlternatives = () => {
  return useMutation({
    mutationFn: (data: { expenseId: number, radiusKm?: number }) => storesApi.getCheaperAlternatives(data.expenseId, data.radiusKm),
  });
};

export const useRecommendations = () => {
  return useQuery({
    queryKey: ['recommendations'],
    queryFn: () => recommendationsApi.get(),
  });
};

// --- Budgets Hooks ---
export const useBudgets = (month?: string) => {
  return useQuery({
    queryKey: ['budgets', month],
    queryFn: () => budgetsApi.getAll(month),
  });
};

export const useUpdateBudget = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: budgetsApi.createOrUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
      queryClient.invalidateQueries({ queryKey: ['analytics', 'budgetVsActual'] });
      queryClient.invalidateQueries({ queryKey: ['healthScore'] });
      toast.success('Budget updated');
    },
  });
};

// --- Profile & Parent Hooks ---
export const useProfile = () => {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => profileApi.get(),
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: profileApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      toast.success('Profile updated');
    },
  });
};

export const useChildren = () => {
  return useQuery({
    queryKey: ['parent', 'children'],
    queryFn: () => parentApi.getChildren(),
  });
};

export const useChildSummary = (childId: number) => {
  return useQuery({
    queryKey: ['parent', 'childSummary', childId],
    queryFn: () => parentApi.getChildSummary(childId),
    enabled: !!childId,
  });
};
