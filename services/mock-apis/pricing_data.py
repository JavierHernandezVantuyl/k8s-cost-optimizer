AWS_PRICING = {
    "instances": {
        "t3.micro": {
            "family": "t3",
            "cpu_cores": 2,
            "memory_gb": 1,
            "hourly_cost": 0.0104,
            "storage_included_gb": 0,
            "network_performance": "low to moderate"
        },
        "t3.small": {
            "family": "t3",
            "cpu_cores": 2,
            "memory_gb": 2,
            "hourly_cost": 0.0208,
            "storage_included_gb": 0,
            "network_performance": "low to moderate"
        },
        "t3.medium": {
            "family": "t3",
            "cpu_cores": 2,
            "memory_gb": 4,
            "hourly_cost": 0.0416,
            "storage_included_gb": 0,
            "network_performance": "low to moderate"
        },
        "t3.large": {
            "family": "t3",
            "cpu_cores": 2,
            "memory_gb": 8,
            "hourly_cost": 0.0832,
            "storage_included_gb": 0,
            "network_performance": "low to moderate"
        },
        "m5.large": {
            "family": "m5",
            "cpu_cores": 2,
            "memory_gb": 8,
            "hourly_cost": 0.096,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "m5.xlarge": {
            "family": "m5",
            "cpu_cores": 4,
            "memory_gb": 16,
            "hourly_cost": 0.192,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "m5.2xlarge": {
            "family": "m5",
            "cpu_cores": 8,
            "memory_gb": 32,
            "hourly_cost": 0.384,
            "storage_included_gb": 0,
            "network_performance": "high"
        },
        "c5.large": {
            "family": "c5",
            "cpu_cores": 2,
            "memory_gb": 4,
            "hourly_cost": 0.085,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "c5.xlarge": {
            "family": "c5",
            "cpu_cores": 4,
            "memory_gb": 8,
            "hourly_cost": 0.17,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "c5.2xlarge": {
            "family": "c5",
            "cpu_cores": 8,
            "memory_gb": 16,
            "hourly_cost": 0.34,
            "storage_included_gb": 0,
            "network_performance": "high"
        }
    },
    "storage": {
        "gp3_per_gb": 0.08,
        "io2_per_gb": 0.125,
        "snapshot_per_gb": 0.05
    },
    "network": {
        "egress_per_gb": 0.09,
        "inter_az_per_gb": 0.01,
        "inter_region_per_gb": 0.02
    },
    "regions": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
}

GCP_PRICING = {
    "instances": {
        "e2-micro": {
            "family": "e2",
            "cpu_cores": 2,
            "memory_gb": 1,
            "hourly_cost": 0.0084,
            "storage_included_gb": 0,
            "network_performance": "low"
        },
        "e2-small": {
            "family": "e2",
            "cpu_cores": 2,
            "memory_gb": 2,
            "hourly_cost": 0.0168,
            "storage_included_gb": 0,
            "network_performance": "low"
        },
        "e2-medium": {
            "family": "e2",
            "cpu_cores": 2,
            "memory_gb": 4,
            "hourly_cost": 0.0336,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "n1-standard-1": {
            "family": "n1",
            "cpu_cores": 1,
            "memory_gb": 3.75,
            "hourly_cost": 0.0475,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "n1-standard-2": {
            "family": "n1",
            "cpu_cores": 2,
            "memory_gb": 7.5,
            "hourly_cost": 0.095,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "n1-standard-4": {
            "family": "n1",
            "cpu_cores": 4,
            "memory_gb": 15,
            "hourly_cost": 0.19,
            "storage_included_gb": 0,
            "network_performance": "high"
        },
        "n2-standard-2": {
            "family": "n2",
            "cpu_cores": 2,
            "memory_gb": 8,
            "hourly_cost": 0.0971,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "n2-standard-4": {
            "family": "n2",
            "cpu_cores": 4,
            "memory_gb": 16,
            "hourly_cost": 0.1942,
            "storage_included_gb": 0,
            "network_performance": "high"
        },
        "n2-standard-8": {
            "family": "n2",
            "cpu_cores": 8,
            "memory_gb": 32,
            "hourly_cost": 0.3884,
            "storage_included_gb": 0,
            "network_performance": "high"
        }
    },
    "storage": {
        "pd_standard_per_gb": 0.04,
        "pd_ssd_per_gb": 0.17,
        "snapshot_per_gb": 0.026
    },
    "network": {
        "egress_per_gb": 0.085,
        "inter_zone_per_gb": 0.01,
        "inter_region_per_gb": 0.01
    },
    "regions": ["us-central1", "us-east1", "europe-west1", "asia-southeast1"]
}

AZURE_PRICING = {
    "instances": {
        "B1s": {
            "family": "B",
            "cpu_cores": 1,
            "memory_gb": 1,
            "hourly_cost": 0.0104,
            "storage_included_gb": 0,
            "network_performance": "low"
        },
        "B2s": {
            "family": "B",
            "cpu_cores": 2,
            "memory_gb": 4,
            "hourly_cost": 0.0416,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "B2ms": {
            "family": "B",
            "cpu_cores": 2,
            "memory_gb": 8,
            "hourly_cost": 0.0832,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "Standard_D2s_v3": {
            "family": "D",
            "cpu_cores": 2,
            "memory_gb": 8,
            "hourly_cost": 0.096,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "Standard_D4s_v3": {
            "family": "D",
            "cpu_cores": 4,
            "memory_gb": 16,
            "hourly_cost": 0.192,
            "storage_included_gb": 0,
            "network_performance": "high"
        },
        "Standard_D8s_v3": {
            "family": "D",
            "cpu_cores": 8,
            "memory_gb": 32,
            "hourly_cost": 0.384,
            "storage_included_gb": 0,
            "network_performance": "high"
        },
        "Standard_F2s_v2": {
            "family": "F",
            "cpu_cores": 2,
            "memory_gb": 4,
            "hourly_cost": 0.085,
            "storage_included_gb": 0,
            "network_performance": "moderate"
        },
        "Standard_F4s_v2": {
            "family": "F",
            "cpu_cores": 4,
            "memory_gb": 8,
            "hourly_cost": 0.169,
            "storage_included_gb": 0,
            "network_performance": "high"
        },
        "Standard_F8s_v2": {
            "family": "F",
            "cpu_cores": 8,
            "memory_gb": 16,
            "hourly_cost": 0.338,
            "storage_included_gb": 0,
            "network_performance": "high"
        }
    },
    "storage": {
        "standard_ssd_per_gb": 0.075,
        "premium_ssd_per_gb": 0.135,
        "snapshot_per_gb": 0.05
    },
    "network": {
        "egress_per_gb": 0.087,
        "inter_zone_per_gb": 0.01,
        "inter_region_per_gb": 0.02
    },
    "regions": ["eastus", "westus2", "northeurope", "southeastasia"]
}

PRICING_DATA = {
    "aws": AWS_PRICING,
    "gcp": GCP_PRICING,
    "azure": AZURE_PRICING
}
