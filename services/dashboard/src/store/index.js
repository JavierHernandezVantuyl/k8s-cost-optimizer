import { create } from 'zustand';

export const useStore = create((set, get) => ({
  demoMode: true,
  summary: null,
  recommendations: [],
  savingsHistory: null,
  loading: false,
  error: null,

  setDemoMode: (demoMode) => set({ demoMode }),
  setSummary: (summary) => set({ summary }),
  setRecommendations: (recommendations) => set({ recommendations }),
  setSavingsHistory: (savingsHistory) => set({ savingsHistory }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  refreshData: async () => {
    const { demoMode } = get();
    set({ loading: true, error: null });

    try {
      if (demoMode) {
        const { api } = await import('../services/api');
        const demoData = api.getDemoData();
        set({ summary: demoData, recommendations: demoData.top_recommendations, loading: false });
      } else {
        const { api } = await import('../services/api');
        const summary = await api.analyzeWorkloads();
        const recommendations = await api.getRecommendations({ limit: 100 });
        set({ summary, recommendations: recommendations.recommendations || [], loading: false });
      }
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
}));

export default useStore;
