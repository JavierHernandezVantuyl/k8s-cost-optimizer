import React from 'react';
import { useStore } from '../store';
import { useWebSocket } from '../hooks/useWebSocket';
import CostCard from '../components/CostCard';
import { SavingsLineChart, ClusterBarChart, OptimizationPieChart } from '../components/SavingsChart';
import { calculations } from '../services/calculations';
import { FiRefreshCw, FiDownload } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { exportService } from '../services/export';
import { api } from '../services/api';

const Dashboard = () => {
  const { summary, loading, refreshData } = useStore();
  const { connected, lastMessage } = useWebSocket();

  const handleExportCSV = async () => {
    try {
      const data = await api.exportToCSV();
      exportService.downloadCSV(data);
      toast.success('CSV exported successfully');
    } catch (error) {
      toast.error('Failed to export CSV');
    }
  };

  const handleExportTerraform = async () => {
    try {
      const data = await api.exportToTerraform();
      exportService.downloadJSON(data);
      toast.success('Terraform config exported');
    } catch (error) {
      toast.error('Failed to export Terraform');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div></div>;
  }

  if (!summary) return <div className="text-center py-12">No data available. Click refresh to load data.</div>;

  const savingsData = Array.from({ length: 12 }, (_, i) => ({
    date: new Date(2024, i, 1).toLocaleDateString('en-US', { month: 'short' }),
    savings: Math.random() * 5000 + 2000,
  }));

  const clusterData = summary.clusters.map((c) => ({
    cluster: c.cluster_name,
    current: c.current_monthly_cost,
    optimized: c.optimized_monthly_cost,
  }));

  const pieData = Object.entries(summary.by_optimization_type || {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value,
  }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Cost Optimization Dashboard</h1>
        <div className="flex gap-2">
          <button onClick={refreshData} className="btn-secondary flex items-center gap-2">
            <FiRefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button onClick={handleExportCSV} className="btn-secondary flex items-center gap-2">
            <FiDownload className="w-4 h-4" />
            Export CSV
          </button>
          <button onClick={handleExportTerraform} className="btn-primary flex items-center gap-2">
            <FiDownload className="w-4 h-4" />
            Export Terraform
          </button>
        </div>
      </div>

      {connected && <div className="bg-green-50 dark:bg-green-900 text-green-800 dark:text-green-200 px-4 py-2 rounded-lg text-sm">Real-time updates enabled</div>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <CostCard title="Monthly Cost" current={summary.total_current_monthly_cost} optimized={summary.total_optimized_monthly_cost} />
        <CostCard title="Yearly Cost" current={summary.total_current_monthly_cost * 12} optimized={summary.total_optimized_monthly_cost * 12} />
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Workloads</h3>
          <p className="text-4xl font-bold text-primary-600">{summary.total_workloads}</p>
          <p className="text-sm text-gray-500 mt-2">Across {summary.clusters.length} clusters</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Savings Trend</h3>
          <SavingsLineChart data={savingsData} />
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Cluster Comparison</h3>
          <ClusterBarChart data={clusterData} />
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Optimization Types Distribution</h3>
        <OptimizationPieChart data={pieData} />
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Top Recommendations</h3>
        <div className="space-y-3">
          {summary.top_recommendations.slice(0, 5).map((rec) => (
            <div key={rec.id} className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div>
                <p className="font-medium">{rec.workload_name}</p>
                <p className="text-sm text-gray-500">{rec.cluster_name} - {rec.optimization_type}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-success-600">{calculations.formatCurrency(rec.monthly_savings)}</p>
                <p className="text-sm text-gray-500">{calculations.formatPercentage(rec.savings_percentage)} savings</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
