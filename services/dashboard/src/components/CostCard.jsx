import React from 'react';
import { FiTrendingDown, FiDollarSign } from 'react-icons/fi';
import { calculations } from '../services/calculations';

export const CostCard = ({ title, current, optimized, icon: Icon = FiDollarSign }) => {
  const savings = current - optimized;
  const percentage = calculations.calculateSavingsPercentage(current, optimized);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <Icon className="w-6 h-6 text-primary-600" />
      </div>
      <div className="space-y-2">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Current</p>
          <p className="text-2xl font-bold">{calculations.formatCurrency(current)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Optimized</p>
          <p className="text-2xl font-bold text-primary-600">{calculations.formatCurrency(optimized)}</p>
        </div>
        <div className="flex items-center gap-2 pt-2 text-success-600">
          <FiTrendingDown className="w-5 h-5" />
          <span className="text-lg font-semibold">{calculations.formatCurrency(savings)} / month</span>
          <span className="text-sm">({calculations.formatPercentage(percentage)})</span>
        </div>
      </div>
    </div>
  );
};

export default CostCard;
