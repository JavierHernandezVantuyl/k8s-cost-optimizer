import React from 'react';
import { useStore } from '../store';
import { SavingsLineChart, SavingsAreaChart } from '../components/SavingsChart';
import { calculations } from '../services/calculations';

const Savings = () => {
  const { summary } = useStore();

  const savingsData = Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    savings: Math.random() * 5000 + 2000,
    current: Math.random() * 15000 + 10000,
    optimized: Math.random() * 10000 + 5000,
  }));

  if (!summary) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Savings History</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm text-gray-500">Monthly Savings</h3>
          <p className="text-3xl font-bold text-success-600">{calculations.formatCurrency(summary.total_potential_monthly_savings)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500">Yearly Savings</h3>
          <p className="text-3xl font-bold text-success-600">{calculations.formatCurrency(summary.total_potential_yearly_savings)}</p>
        </div>
        <div className="card">
          <h3 className="text-sm text-gray-500">Savings Percentage</h3>
          <p className="text-3xl font-bold text-success-600">{summary.overall_savings_percentage.toFixed(1)}%</p>
        </div>
      </div>
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Savings Over Time</h3>
        <SavingsLineChart data={savingsData} />
      </div>
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Cost Comparison</h3>
        <SavingsAreaChart data={savingsData} />
      </div>
    </div>
  );
};

export default Savings;
