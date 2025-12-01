export const calculations = {
  calculateSavingsPercentage(currentCost, optimizedCost) {
    if (currentCost === 0) return 0;
    return ((currentCost - optimizedCost) / currentCost) * 100;
  },

  calculateTotalSavings(recommendations) {
    return recommendations.reduce((sum, rec) => sum + (rec.monthly_savings || 0), 0);
  },

  calculateAverageSavingsPercentage(recommendations) {
    if (recommendations.length === 0) return 0;
    const totalPercentage = recommendations.reduce(
      (sum, rec) => sum + (rec.savings_percentage || 0),
      0
    );
    return totalPercentage / recommendations.length;
  },

  groupByCluster(recommendations) {
    return recommendations.reduce((groups, rec) => {
      const cluster = rec.cluster_name || 'unknown';
      if (!groups[cluster]) {
        groups[cluster] = [];
      }
      groups[cluster].push(rec);
      return groups;
    }, {});
  },

  groupByOptimizationType(recommendations) {
    return recommendations.reduce((groups, rec) => {
      const type = rec.optimization_type || 'unknown';
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(rec);
      return groups;
    }, {});
  },

  calculateMonthlySavingsByType(recommendations) {
    const byType = this.groupByOptimizationType(recommendations);
    return Object.entries(byType).reduce((result, [type, recs]) => {
      result[type] = this.calculateTotalSavings(recs);
      return result;
    }, {});
  },

  calculateRiskDistribution(recommendations) {
    return recommendations.reduce((dist, rec) => {
      const level = rec.risk_assessment?.level || 'UNKNOWN';
      dist[level] = (dist[level] || 0) + 1;
      return dist;
    }, {});
  },

  calculateConfidenceDistribution(recommendations) {
    const ranges = {
      high: 0,
      medium: 0,
      low: 0,
    };

    recommendations.forEach((rec) => {
      const score = rec.confidence_score || 0;
      if (score >= 0.8) ranges.high++;
      else if (score >= 0.6) ranges.medium++;
      else ranges.low++;
    });

    return ranges;
  },

  formatCurrency(amount, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(amount);
  },

  formatNumber(number, decimals = 0) {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(number);
  },

  formatPercentage(percentage, decimals = 1) {
    return `${percentage.toFixed(decimals)}%`;
  },

  calculateProjectedAnnualSavings(monthlySavings) {
    return monthlySavings * 12;
  },

  calculateROI(currentCost, optimizedCost, implementationCost = 0) {
    const savings = currentCost - optimizedCost;
    if (implementationCost === 0) return Infinity;
    return (savings / implementationCost) * 100;
  },

  calculatePaybackPeriod(monthlySavings, implementationCost = 0) {
    if (monthlySavings === 0) return Infinity;
    return implementationCost / monthlySavings;
  },

  getOptimizationTypeBadgeColor(type) {
    const colors = {
      right_size_cpu: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      right_size_memory: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      reduce_replicas: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      spot_instances: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      remove_unused: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      scheduled_scaling: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
      change_instance_type: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
    };
    return colors[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  },

  getRiskLevelColor(level) {
    const colors = {
      LOW: 'text-green-600 dark:text-green-400',
      MEDIUM: 'text-yellow-600 dark:text-yellow-400',
      HIGH: 'text-orange-600 dark:text-orange-400',
      CRITICAL: 'text-red-600 dark:text-red-400',
    };
    return colors[level] || 'text-gray-600 dark:text-gray-400';
  },

  getStatusColor(status) {
    const colors = {
      pending: 'text-gray-600 dark:text-gray-400',
      analyzing: 'text-blue-600 dark:text-blue-400',
      ready: 'text-green-600 dark:text-green-400',
      applying: 'text-yellow-600 dark:text-yellow-400',
      applied: 'text-green-600 dark:text-green-400',
      failed: 'text-red-600 dark:text-red-400',
    };
    return colors[status] || 'text-gray-600 dark:text-gray-400';
  },
};

export default calculations;
