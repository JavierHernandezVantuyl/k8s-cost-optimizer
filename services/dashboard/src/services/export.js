export const exportService = {
  downloadCSV(data, filename = 'cost-optimization-recommendations.csv') {
    const blob = new Blob([data], { type: 'text/csv;charset=utf-8;' });
    this.downloadBlob(blob, filename);
  },

  downloadJSON(data, filename = 'terraform.tf.json') {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    this.downloadBlob(blob, filename);
  },

  downloadYAML(data, filename = 'optimizations.yaml') {
    const yamlString = this.convertToYAML(data);
    const blob = new Blob([yamlString], { type: 'text/yaml' });
    this.downloadBlob(blob, filename);
  },

  downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  convertToYAML(data, indent = 0) {
    const indentStr = '  '.repeat(indent);
    let yaml = '';

    if (Array.isArray(data)) {
      data.forEach((item) => {
        yaml += `${indentStr}- ${this.convertToYAML(item, indent + 1).trim()}\n`;
      });
    } else if (typeof data === 'object' && data !== null) {
      Object.entries(data).forEach(([key, value]) => {
        if (typeof value === 'object' && value !== null) {
          yaml += `${indentStr}${key}:\n${this.convertToYAML(value, indent + 1)}`;
        } else {
          yaml += `${indentStr}${key}: ${value}\n`;
        }
      });
    } else {
      return String(data);
    }

    return yaml;
  },

  convertRecommendationsToCSV(recommendations) {
    const headers = [
      'Cluster',
      'Namespace',
      'Workload',
      'Optimization Type',
      'Current Monthly Cost',
      'Optimized Monthly Cost',
      'Monthly Savings',
      'Savings %',
      'Confidence Score',
      'Risk Level',
      'Status',
    ];

    const rows = recommendations.map((rec) => [
      rec.cluster_name,
      rec.namespace,
      rec.workload_name,
      rec.optimization_type,
      `$${rec.current_cost.monthly.toFixed(2)}`,
      `$${rec.optimized_cost.monthly.toFixed(2)}`,
      `$${rec.monthly_savings.toFixed(2)}`,
      `${rec.savings_percentage.toFixed(1)}%`,
      rec.confidence_score.toFixed(2),
      rec.risk_assessment.level,
      rec.status,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    return csvContent;
  },

  convertToTerraform(recommendations) {
    const terraform = {
      terraform: {
        required_version: '>= 1.0',
      },
      resource: {},
    };

    recommendations.slice(0, 5).forEach((rec) => {
      const resourceName = `k8s_deployment_${rec.workload_name.replace(/-/g, '_')}`;
      terraform.resource[resourceName] = {
        metadata: {
          name: rec.workload_name,
          namespace: rec.namespace,
        },
        spec: {
          replicas: rec.recommended_config?.replicas || 1,
          template: {
            spec: {
              containers: [
                {
                  resources: {
                    requests: {
                      cpu: rec.recommended_config?.cpu_request,
                      memory: rec.recommended_config?.memory_request,
                    },
                  },
                },
              ],
            },
          },
        },
      };
    });

    return terraform;
  },
};

export default exportService;
