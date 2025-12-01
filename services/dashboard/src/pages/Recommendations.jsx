import React from 'react';
import { useStore } from '../store';
import { calculations } from '../services/calculations';
import toast from 'react-hot-toast';

const Recommendations = () => {
  const { recommendations } = useStore();

  const handleApply = (rec) => {
    toast.success(`Applied optimization for ${rec.workload_name}`);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Optimization Recommendations</h1>
      <div className="space-y-4">
        {recommendations.map((rec) => (
          <div key={rec.id} className="card">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{rec.workload_name}</h3>
                <p className="text-sm text-gray-500">{rec.cluster_name} / {rec.namespace}</p>
                <div className="mt-3 flex items-center gap-4">
                  <span className={`px-2 py-1 text-xs rounded ${calculations.getOptimizationTypeBadgeColor(rec.optimization_type)}`}>{rec.optimization_type}</span>
                  <span className={`text-sm font-medium ${calculations.getRiskLevelColor(rec.risk_assessment.level)}`}>{rec.risk_assessment.level} Risk</span>
                  <span className="text-sm text-gray-500">Confidence: {(rec.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-success-600">{calculations.formatCurrency(rec.monthly_savings)}</p>
                <p className="text-sm text-gray-500">/ month</p>
                <button onClick={() => handleApply(rec)} className="mt-2 btn-primary text-sm">Apply</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Recommendations;
