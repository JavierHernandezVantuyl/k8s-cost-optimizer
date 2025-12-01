import React from 'react';
import { useStore } from '../store';
import { calculations } from '../services/calculations';
import { FiServer } from 'react-icons/fi';

const Clusters = () => {
  const { summary } = useStore();

  if (!summary) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Cluster Management</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {summary.clusters.map((cluster) => (
          <div key={cluster.cluster_name} className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <FiServer className="w-6 h-6 text-primary-600" />
                <h3 className="text-lg font-semibold">{cluster.cluster_name}</h3>
              </div>
              <span className="text-xs bg-primary-100 text-primary-800 px-2 py-1 rounded">{cluster.provider}</span>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500">Workloads</p>
                <p className="text-2xl font-bold">{cluster.workload_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Current Cost</p>
                <p className="text-xl font-semibold">{calculations.formatCurrency(cluster.current_monthly_cost)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Potential Savings</p>
                <p className="text-xl font-semibold text-success-600">{calculations.formatCurrency(cluster.potential_monthly_savings)}</p>
                <p className="text-sm text-gray-500">{calculations.formatPercentage(cluster.savings_percentage)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Recommendations</p>
                <p className="text-lg font-medium">{cluster.recommendation_count}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Clusters;
