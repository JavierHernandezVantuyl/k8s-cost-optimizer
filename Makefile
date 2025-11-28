.PHONY: help setup start stop clean status logs health-check clusters clusters-clean deploy-operator test-operator operator-logs

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
	@echo "  deploy-operator - Deploy cost optimization operator to all clusters"
	@echo "  test-operator  - Run operator test suite"
	@echo "  operator-logs  - View operator logs"
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
	@echo "  Grafana:    http://localhost:3000 (admin/admin123)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  MinIO:      http://localhost:9001 (minioadmin/minioadmin123)"
	@echo "  PostgreSQL: localhost:5432 (optimizer/optimizer_dev_pass)"
	@echo "  Redis:      localhost:6379"
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

deploy-operator:
	@echo "==> Deploying Cost Optimization Operator to all clusters..."
	@for cluster in aws-cluster gcp-cluster azure-cluster; do \
		echo ""; \
		echo "Deploying to $$cluster..."; \
		bash services/operator/deploy.sh $$cluster; \
	done
	@echo ""
	@echo "==> Operator deployed to all clusters!"
	@echo ""
	@echo "View operator status:"
	@echo "  make operator-logs"
	@echo ""
	@echo "Apply example optimization:"
	@echo "  kubectl apply -f services/operator/manifests/examples/cpu-optimization.yaml"

test-operator:
	@echo "==> Running operator test suite..."
	@bash services/operator/tests/test_operator.sh aws-cluster

operator-logs:
	@echo "==> Viewing operator logs (Ctrl+C to exit)..."
	@kubectl config use-context kind-aws-cluster
	@kubectl logs -n cost-optimizer -l app=cost-optimizer-operator -f
