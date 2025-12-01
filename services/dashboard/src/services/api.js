import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const api = {
  async analyzeWorkloads(filters = {}) {
    const response = await apiClient.post('/analyze', filters);
    return response.data;
  },

  async getRecommendations(params = {}) {
    const response = await apiClient.get('/recommendations', { params });
    return response.data;
  },

  async optimizeWorkload(workloadId, options = {}) {
    const response = await apiClient.post(`/optimize/${workloadId}`, options);
    return response.data;
  },

  async applyRecommendation(recommendationId, dryRun = false) {
    const response = await apiClient.post(`/apply/${recommendationId}`, { dry_run: dryRun });
    return response.data;
  },

  async getSavingsHistory(days = 30) {
    const response = await apiClient.get(`/savings/history?days=${days}`);
    return response.data;
  },

  async exportToCSV() {
    const response = await apiClient.get('/export/csv', {
      responseType: 'blob',
    });
    return response.data;
  },

  async exportToTerraform() {
    const response = await apiClient.post('/export/terraform');
    return response.data;
  },

  async getHealth() {
    const response = await apiClient.get('/health');
    return response.data;
  },

  getDemoData() {
    return {
      total_workloads: 53,
      total_current_monthly_cost: 12450.00,
      total_optimized_monthly_cost: 7890.00,
      total_potential_monthly_savings: 4560.00,
      total_potential_yearly_savings: 54720.00,
      overall_savings_percentage: 36.6,
      clusters: [
        {
          cluster_name: 'aws-cluster',
          provider: 'aws',
          workload_count: 25,
          current_monthly_cost: 6200.00,
          optimized_monthly_cost: 3950.00,
          potential_monthly_savings: 2250.00,
          savings_percentage: 36.3,
          recommendation_count: 18,
        },
        {
          cluster_name: 'gcp-cluster',
          provider: 'gcp',
          workload_count: 15,
          current_monthly_cost: 3750.00,
          optimized_monthly_cost: 2340.00,
          potential_monthly_savings: 1410.00,
          savings_percentage: 37.6,
          recommendation_count: 12,
        },
        {
          cluster_name: 'azure-cluster',
          provider: 'azure',
          workload_count: 13,
          current_monthly_cost: 2500.00,
          optimized_monthly_cost: 1600.00,
          potential_monthly_savings: 900.00,
          savings_percentage: 36.0,
          recommendation_count: 10,
        },
      ],
      top_recommendations: [
        {
          id: 'rec-1',
          workload_name: 'frontend-web',
          cluster_name: 'aws-cluster',
          namespace: 'production',
          optimization_type: 'right_size_cpu',
          current_cost: { monthly: 876.00, yearly: 10512.00 },
          optimized_cost: { monthly: 438.00, yearly: 5256.00 },
          monthly_savings: 438.00,
          yearly_savings: 5256.00,
          savings_percentage: 50.0,
          confidence_score: 0.92,
          risk_assessment: { level: 'LOW', score: 0.3 },
          status: 'pending',
        },
        {
          id: 'rec-2',
          workload_name: 'api-gateway',
          cluster_name: 'aws-cluster',
          namespace: 'production',
          optimization_type: 'reduce_replicas',
          current_cost: { monthly: 1168.00, yearly: 14016.00 },
          optimized_cost: { monthly: 730.00, yearly: 8760.00 },
          monthly_savings: 438.00,
          yearly_savings: 5256.00,
          savings_percentage: 37.5,
          confidence_score: 0.88,
          risk_assessment: { level: 'LOW', score: 0.25 },
          status: 'pending',
        },
        {
          id: 'rec-3',
          workload_name: 'batch-processor',
          cluster_name: 'gcp-cluster',
          namespace: 'production',
          optimization_type: 'spot_instances',
          current_cost: { monthly: 2920.00, yearly: 35040.00 },
          optimized_cost: { monthly: 876.00, yearly: 10512.00 },
          monthly_savings: 2044.00,
          yearly_savings: 24528.00,
          savings_percentage: 70.0,
          confidence_score: 0.85,
          risk_assessment: { level: 'MEDIUM', score: 0.5 },
          status: 'pending',
        },
        {
          id: 'rec-4',
          workload_name: 'microservice-analytics',
          cluster_name: 'azure-cluster',
          namespace: 'production',
          optimization_type: 'scheduled_scaling',
          current_cost: { monthly: 438.00, yearly: 5256.00 },
          optimized_cost: { monthly: 263.00, yearly: 3156.00 },
          monthly_savings: 175.00,
          yearly_savings: 2100.00,
          savings_percentage: 40.0,
          confidence_score: 0.82,
          risk_assessment: { level: 'LOW', score: 0.3 },
          status: 'pending',
        },
        {
          id: 'rec-5',
          workload_name: 'dev-testing-env',
          cluster_name: 'aws-cluster',
          namespace: 'development',
          optimization_type: 'remove_unused',
          current_cost: { monthly: 657.00, yearly: 7884.00 },
          optimized_cost: { monthly: 0.00, yearly: 0.00 },
          monthly_savings: 657.00,
          yearly_savings: 7884.00,
          savings_percentage: 100.0,
          confidence_score: 0.78,
          risk_assessment: { level: 'LOW', score: 0.2 },
          status: 'pending',
        },
      ],
      by_optimization_type: {
        right_size_cpu: 1250.00,
        right_size_memory: 980.00,
        reduce_replicas: 658.00,
        spot_instances: 2044.00,
        remove_unused: 657.00,
        scheduled_scaling: 421.00,
        change_instance_type: 150.00,
      },
    };
  },
};

export default api;
