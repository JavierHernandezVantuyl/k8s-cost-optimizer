import React, { useState } from 'react';
import { useStore } from '../store';
import { calculations } from '../services/calculations';

const Workloads = () => {
  const { recommendations } = useStore();
  const [filter, setFilter] = useState('all');

  const filtered = filter === 'all' ? recommendations : recommendations.filter((r) => r.cluster_name === filter);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Workloads</h1>
      <div className="flex gap-2">
        <button onClick={() => setFilter('all')} className={filter === 'all' ? 'btn-primary' : 'btn-secondary'}>All</button>
        <button onClick={() => setFilter('aws-cluster')} className={filter === 'aws-cluster' ? 'btn-primary' : 'btn-secondary'}>AWS</button>
        <button onClick={() => setFilter('gcp-cluster')} className={filter === 'gcp-cluster' ? 'btn-primary' : 'btn-secondary'}>GCP</button>
        <button onClick={() => setFilter('azure-cluster')} className={filter === 'azure-cluster' ? 'btn-primary' : 'btn-secondary'}>Azure</button>
      </div>
      <div className="card overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="px-4 py-3 text-left text-sm font-medium">Workload</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Cluster</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Type</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Savings</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((rec) => (
              <tr key={rec.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-4 py-3 text-sm font-medium">{rec.workload_name}</td>
                <td className="px-4 py-3 text-sm">{rec.cluster_name}</td>
                <td className="px-4 py-3"><span className={`px-2 py-1 text-xs rounded ${calculations.getOptimizationTypeBadgeColor(rec.optimization_type)}`}>{rec.optimization_type}</span></td>
                <td className="px-4 py-3 text-sm text-right font-semibold text-success-600">{calculations.formatCurrency(rec.monthly_savings)}</td>
                <td className="px-4 py-3 text-sm text-right">{(rec.confidence_score * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Workloads;
