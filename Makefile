.PHONY: help setup start stop clean status logs health-check clusters clusters-clean deploy-monitoring test-optimizer test-pricing test-metrics

help:
	@echo "K8s Cost Optimizer - Infrastructure Management"
	@echo ""
	@echo "Available targets:"
	@echo "  setup          - Install dependencies and create Kind clusters"
	@echo "  start          - Start all Docker services"
	@echo "  stop           - Stop all Docker services"
	@echo "  clean          - Complete cleanup (stop services and remove clusters)"
	@echo "  status         - Show status of all components"
	@echo "  logs           - Tail logs from all services"
	@echo "  health-check   - Verify all services are running properly"
	@echo "  clusters       - Create Kind clusters only"
	@echo "  clusters-clean - Remove Kind clusters only"
	@echo "  deploy-monitoring - Deploy monitoring to Kind clusters"
	@echo "  test-optimizer - Test the optimizer API"
	@echo "  test-pricing   - Test pricing APIs"
	@echo "  test-metrics   - Test metrics generator"
	@echo ""

setup:
	@echo "==> Checking prerequisites..."
	@command -v docker >/dev/null 2>&1 || { echo "Error: docker is not installed" >&2; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "Error: docker-compose is not installed" >&2; exit 1; }
	@command -v kind >/dev/null 2>&1 || { echo "Error: kind is not installed. Install from https://kind.sigs.k8s.io/" >&2; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl is not installed" >&2; exit 1; }
	@echo "==> All prerequisites satisfied"
	@echo "==> Creating Kind clusters..."
	@bash scripts/setup-clusters.sh
	@echo "==> Setup complete!"

start:
	@echo "==> Starting Docker services..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose up -d; \
	else \
		docker compose up -d; \
	fi
	@echo "==> Waiting for services to be healthy..."
	@sleep 5
	@$(MAKE) health-check
	@echo ""
	@echo "==> All services started successfully!"
	@echo ""
	@echo "Service URLs:"
	@echo "  Optimizer API:   http://localhost:8000"
	@echo "  Metrics Gen:     http://localhost:8001"
	@echo "  Grafana:         http://localhost:3000 (admin/admin123)"
	@echo "  Prometheus:      http://localhost:9090"
	@echo "  MinIO Console:   http://localhost:9001 (minioadmin/minioadmin123)"
	@echo "  AWS Pricing:     http://localhost:5001"
	@echo "  GCP Pricing:     http://localhost:5002"
	@echo "  Azure Pricing:   http://localhost:5003"
	@echo "  PostgreSQL:      localhost:5432 (optimizer/optimizer_dev_pass)"
	@echo "  Redis:           localhost:6379"
	@echo ""

stop:
	@echo "==> Stopping Docker services..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose down; \
	else \
		docker compose down; \
	fi
	@echo "==> Services stopped"

clean:
	@echo "==> Starting complete cleanup..."
	@$(MAKE) stop
	@echo "==> Removing Docker volumes..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose down -v; \
	else \
		docker compose down -v; \
	fi
	@echo "==> Removing Kind clusters..."
	@bash scripts/cleanup.sh
	@echo "==> Cleanup complete!"

status:
	@echo "==> Docker Services Status:"
	@echo ""
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose ps; \
	else \
		docker compose ps; \
	fi
	@echo ""
	@echo "==> Kind Clusters:"
	@echo ""
	@kind get clusters 2>/dev/null || echo "No clusters found"
	@echo ""
	@for cluster in aws-cluster gcp-cluster azure-cluster; do \
		if kind get clusters 2>/dev/null | grep -q "^$$cluster$$"; then \
			echo "Cluster: $$cluster"; \
			kubectl get nodes --context kind-$$cluster 2>/dev/null | grep -v "^NAME" | wc -l | xargs echo "  Nodes:"; \
		fi \
	done

logs:
	@echo "==> Tailing logs from all services (Ctrl+C to exit)..."
	@if command -v docker-compose >/dev/null 2>&1; then \
		docker-compose logs -f; \
	else \
		docker compose logs -f; \
	fi

health-check:
	@bash scripts/health-check.sh

clusters:
	@echo "==> Creating Kind clusters..."
	@bash scripts/setup-clusters.sh

clusters-clean:
	@echo "==> Removing Kind clusters..."
	@bash scripts/cleanup.sh

deploy-monitoring:
	@echo "==> Deploying monitoring to Kind clusters..."
	@for cluster in aws-cluster gcp-cluster azure-cluster; do \
		echo "Deploying to $$cluster..."; \
		kubectl apply -f manifests/monitoring/ --context kind-$$cluster; \
	done
	@echo "==> Monitoring deployed to all clusters"

test-optimizer:
	@echo "==> Testing Optimizer API..."
	@echo ""
	@echo "1. Health check:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Service not ready"
	@echo ""
	@echo "2. Running sample optimization scenarios:"
	@cd services/optimizer-api && python3 tests/sample_data.py

test-pricing:
	@echo "==> Testing Pricing APIs..."
	@echo ""
	@echo "AWS Pricing API:"
	@curl -s http://localhost:5001/health | python3 -m json.tool || echo "AWS pricing not ready"
	@echo ""
	@echo "GCP Pricing API:"
	@curl -s http://localhost:5002/health | python3 -m json.tool || echo "GCP pricing not ready"
	@echo ""
	@echo "Azure Pricing API:"
	@curl -s http://localhost:5003/health | python3 -m json.tool || echo "Azure pricing not ready"

test-metrics:
	@echo "==> Testing Metrics Generator..."
	@echo ""
	@curl -s http://localhost:8001/metrics | head -n 20 || echo "Metrics generator not ready"
	@echo ""
	@echo "==> Check Prometheus for metrics at http://localhost:9090"
