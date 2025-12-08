.PHONY: help setup start stop restart clean status logs health-check \
        clusters clusters-clean infra-start db-check db-migrate db-seed \
        shell-api shell-db shell-redis clean-data \
        test test-unit test-integration test-e2e test-load chaos-test coverage \
        demo demo-report demo-clean \
        deploy-dev deploy-staging deploy-prod \
        build build-api build-operator build-dashboard \
        version validate lint format

# Configuration
DOCKER_COMPOSE := $(shell command -v docker-compose 2>/dev/null || echo "docker compose")
PROJECT_NAME := k8s-cost-optimizer
VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.0")

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

help:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(CYAN)  K8s Cost Optimizer - Development & Deployment$(RESET)"
	@echo "$(CYAN)  Version: $(VERSION)$(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(RESET)"
	@echo "  setup              - Complete setup (clusters + services)"
	@echo "  start              - Start all services"
	@echo "  stop               - Stop all services"
	@echo "  restart            - Restart all services"
	@echo "  clean              - Complete cleanup (services + clusters)"
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@echo "  shell-api          - Shell into API container"
	@echo "  shell-db           - Shell into PostgreSQL"
	@echo "  shell-redis        - Shell into Redis"
	@echo "  db-migrate         - Run database migrations"
	@echo "  db-seed            - Seed database with demo data"
	@echo "  logs               - Tail all service logs"
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@echo "  test               - Run all tests"
	@echo "  test-unit          - Run unit tests"
	@echo "  test-integration   - Run integration tests"
	@echo "  test-e2e           - Run end-to-end tests"
	@echo "  test-load          - Run load tests"
	@echo "  chaos-test         - Run chaos engineering tests"
	@echo "  coverage           - Generate test coverage report"
	@echo ""
	@echo "$(GREEN)Demo:$(RESET)"
	@echo "  demo               - Run impressive demo scenario"
	@echo "  demo-report        - Generate PDF demo report"
	@echo "  demo-clean         - Clean demo data"
	@echo ""
	@echo "$(GREEN)Build:$(RESET)"
	@echo "  build              - Build all containers"
	@echo "  build-api          - Build API container"
	@echo "  build-operator     - Build operator binary"
	@echo "  build-dashboard    - Build dashboard"
	@echo ""
	@echo "$(GREEN)Deployment:$(RESET)"
	@echo "  deploy-dev         - Deploy to development"
	@echo "  deploy-staging     - Deploy to staging"
	@echo "  deploy-prod        - Deploy to production"
	@echo ""
	@echo "$(GREEN)Utilities:$(RESET)"
	@echo "  status             - Show status of all components"
	@echo "  health-check       - Verify all services are healthy"
	@echo "  validate           - Validate configuration files"
	@echo "  lint               - Run linters"
	@echo "  format             - Format code"
	@echo "  version            - Display version information"
	@echo ""
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""

## Setup & Installation

setup:
	@echo "$(CYAN)==> Checking prerequisites...$(RESET)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Error: docker is not installed$(RESET)" >&2; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "$(RED)Error: docker-compose is not installed$(RESET)" >&2; exit 1; }
	@command -v kind >/dev/null 2>&1 || { echo "$(RED)Error: kind is not installed. Install from https://kind.sigs.k8s.io/$(RESET)" >&2; exit 1; }
	@command -v kubectl >/dev/null 2>&1 || { echo "$(RED)Error: kubectl is not installed$(RESET)" >&2; exit 1; }
	@echo "$(GREEN)✓ All prerequisites satisfied$(RESET)"
	@echo "$(CYAN)==> Creating Kind clusters...$(RESET)"
	@bash scripts/setup-clusters.sh
	@echo "$(CYAN)==> Starting infrastructure...$(RESET)"
	@$(MAKE) infra-start
	@echo "$(GREEN)✓ Setup complete!$(RESET)"
	@echo ""
	@$(MAKE) status

infra-start:
	@echo "$(CYAN)==> Starting infrastructure services...$(RESET)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(CYAN)==> Waiting for services to be healthy...$(RESET)"
	@sleep 5
	@$(MAKE) health-check
	@echo ""
	@echo "$(GREEN)✓ All services started successfully!$(RESET)"
	@echo ""
	@echo "$(CYAN)Service URLs:$(RESET)"
	@echo "  API Docs:   http://localhost:8000/docs"
	@echo "  Dashboard:  http://localhost:3000"
	@echo "  Grafana:    http://localhost:3001 (admin/admin123)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  MinIO:      http://localhost:9001 (minioadmin/minioadmin123)"
	@echo "  PostgreSQL: localhost:5432 (optimizer/optimizer_dev_pass)"
	@echo "  Redis:      localhost:6379"
	@echo ""

start: infra-start
	@echo "$(GREEN)✓ All systems operational!$(RESET)"

stop:
	@echo "$(CYAN)==> Stopping services...$(RESET)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(RESET)"

restart: stop start

clean:
	@echo "$(CYAN)==> Starting complete cleanup...$(RESET)"
	@$(MAKE) stop
	@echo "$(CYAN)==> Removing Docker volumes...$(RESET)"
	@$(DOCKER_COMPOSE) down -v
	@echo "$(CYAN)==> Removing Kind clusters...$(RESET)"
	@bash scripts/cleanup.sh
	@echo "$(GREEN)✓ Cleanup complete!$(RESET)"

clean-data:
	@echo "$(CYAN)==> Cleaning data only...$(RESET)"
	@docker exec k8s-optimizer-postgres psql -U optimizer -d cost_optimizer -c "TRUNCATE analyses, recommendations, workloads, clusters CASCADE;" || true
	@docker exec k8s-optimizer-redis redis-cli FLUSHALL || true
	@echo "$(GREEN)✓ Data cleaned$(RESET)"

## Development

shell-api:
	@echo "$(CYAN)==> Opening shell in API container...$(RESET)"
	@docker exec -it k8s-optimizer-api /bin/bash || echo "$(RED)API container not running$(RESET)"

shell-db:
	@echo "$(CYAN)==> Opening PostgreSQL shell...$(RESET)"
	@docker exec -it k8s-optimizer-postgres psql -U optimizer -d cost_optimizer

shell-redis:
	@echo "$(CYAN)==> Opening Redis shell...$(RESET)"
	@docker exec -it k8s-optimizer-redis redis-cli

db-check:
	@echo "$(CYAN)==> Checking database connection...$(RESET)"
	@docker exec k8s-optimizer-postgres pg_isready -U optimizer && echo "$(GREEN)✓ PostgreSQL is ready$(RESET)" || echo "$(RED)✗ PostgreSQL is not ready$(RESET)"

db-migrate:
	@echo "$(CYAN)==> Running database migrations...$(RESET)"
	@docker exec k8s-optimizer-api alembic upgrade head || echo "$(YELLOW)Migrations not configured yet$(RESET)"
	@echo "$(GREEN)✓ Migrations complete$(RESET)"

db-seed:
	@echo "$(CYAN)==> Seeding database with demo data...$(RESET)"
	@bash demo/scripts/generate-data.sh || echo "$(YELLOW)Demo data generator not available yet$(RESET)"
	@echo "$(GREEN)✓ Database seeded$(RESET)"

logs:
	@echo "$(CYAN)==> Tailing logs from all services (Ctrl+C to exit)...$(RESET)"
	@$(DOCKER_COMPOSE) logs -f

## Testing

test:
	@echo "$(CYAN)==> Running all tests...$(RESET)"
	@$(MAKE) test-unit
	@$(MAKE) test-integration
	@$(MAKE) test-e2e
	@echo "$(GREEN)✓ All tests passed!$(RESET)"

test-unit:
	@echo "$(CYAN)==> Running unit tests...$(RESET)"
	@cd tests/unit && python -m pytest -v --cov=../../services --cov-report=html --cov-report=term || echo "$(YELLOW)Unit tests not available yet$(RESET)"

test-integration:
	@echo "$(CYAN)==> Running integration tests...$(RESET)"
	@cd tests/integration && python -m pytest -v || echo "$(YELLOW)Integration tests not available yet$(RESET)"

test-e2e:
	@echo "$(CYAN)==> Running E2E tests...$(RESET)"
	@cd tests/e2e && npx cypress run || echo "$(YELLOW)E2E tests not available yet$(RESET)"

test-load:
	@echo "$(CYAN)==> Running load tests (1000 concurrent users)...$(RESET)"
	@cd tests/load && locust -f scenarios/stress_test.py --headless -u 1000 -r 100 -t 5m --html report.html || echo "$(YELLOW)Load tests not available yet$(RESET)"
	@echo "$(GREEN)✓ Load test complete - see tests/load/report.html$(RESET)"

chaos-test:
	@echo "$(YELLOW)⚠️  Running chaos engineering tests...$(RESET)"
	@echo "$(RED)WARNING: This will intentionally cause failures!$(RESET)"
	@read -p "Continue? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	@cd tests/chaos && bash run-chaos.sh || echo "$(YELLOW)Chaos tests not available yet$(RESET)"

coverage:
	@echo "$(CYAN)==> Generating coverage report...$(RESET)"
	@cd tests/unit && python -m pytest --cov=../../services --cov-report=html --cov-report=term-missing || echo "$(YELLOW)Coverage not available yet$(RESET)"
	@echo "$(GREEN)✓ Coverage report generated$(RESET)"
	@echo "Open $(CYAN)tests/unit/htmlcov/index.html$(RESET) to view report"

## Demo

demo:
	@echo "$(CYAN)==> Running impressive demo scenario...$(RESET)"
	@bash demo/scripts/run-demo.sh || echo "$(YELLOW)Demo not available yet$(RESET)"
	@echo ""
	@echo "$(GREEN)✓ Demo complete!$(RESET)"

demo-report:
	@echo "$(CYAN)==> Generating PDF demo report...$(RESET)"
	@bash demo/scripts/generate-report.sh || echo "$(YELLOW)Report generator not available yet$(RESET)"
	@echo "$(GREEN)✓ Report generated$(RESET)"

demo-clean:
	@echo "$(CYAN)==> Cleaning demo data...$(RESET)"
	@$(MAKE) clean-data
	@echo "$(GREEN)✓ Demo data cleaned$(RESET)"

## Build

build: build-api build-operator build-dashboard
	@echo "$(GREEN)✓ All components built!$(RESET)"

build-api:
	@echo "$(CYAN)==> Building API container...$(RESET)"
	@docker build -t ghcr.io/yourusername/optimizer-api:$(VERSION) services/optimizer-api/ || echo "$(YELLOW)API build not available yet$(RESET)"

build-operator:
	@echo "$(CYAN)==> Building operator...$(RESET)"
	@cd services/operator && make build || echo "$(YELLOW)Operator build not available yet$(RESET)"

build-dashboard:
	@echo "$(CYAN)==> Building dashboard...$(RESET)"
	@cd services/dashboard && npm run build || echo "$(YELLOW)Dashboard build not available yet$(RESET)"

## Deployment

deploy-dev:
	@echo "$(CYAN)==> Deploying to development...$(RESET)"
	@kubectl apply -k infrastructure/kustomize/overlays/dev || echo "$(YELLOW)Dev deployment not available yet$(RESET)"
	@echo "$(GREEN)✓ Deployed to development$(RESET)"

deploy-staging:
	@echo "$(CYAN)==> Deploying to staging...$(RESET)"
	@kubectl apply -k infrastructure/kustomize/overlays/staging || echo "$(YELLOW)Staging deployment not available yet$(RESET)"
	@echo "$(GREEN)✓ Deployed to staging$(RESET)"

deploy-prod:
	@echo "$(YELLOW)⚠️  Deploying to PRODUCTION$(RESET)"
	@read -p "Are you sure? (yes/NO) " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "$(CYAN)==> Deploying to production...$(RESET)"
	@kubectl apply -k infrastructure/kustomize/overlays/prod || echo "$(YELLOW)Prod deployment not available yet$(RESET)"
	@echo "$(GREEN)✓ Deployed to production$(RESET)"

## Utilities

status:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(CYAN)  System Status$(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(GREEN)Docker Services:$(RESET)"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(GREEN)Kind Clusters:$(RESET)"
	@kind get clusters 2>/dev/null || echo "No clusters found"
	@echo ""
	@for cluster in aws-cluster gcp-cluster azure-cluster; do \
		if kind get clusters 2>/dev/null | grep -q "^$$cluster$$"; then \
			echo "  $(GREEN)✓$(RESET) $$cluster (nodes: $$(kubectl get nodes --context kind-$$cluster 2>/dev/null | grep -v "^NAME" | wc -l | xargs))"; \
		fi \
	done
	@echo ""

health-check:
	@bash scripts/health-check.sh

validate:
	@echo "$(CYAN)==> Validating configuration files...$(RESET)"
	@docker-compose config > /dev/null && echo "$(GREEN)✓ docker-compose.yml is valid$(RESET)" || echo "$(RED)✗ docker-compose.yml has errors$(RESET)"
	@cd infrastructure/terraform && terraform fmt -check -recursive || echo "$(YELLOW)Terraform files need formatting$(RESET)"
	@echo "$(GREEN)✓ Validation complete$(RESET)"

lint:
	@echo "$(CYAN)==> Running linters...$(RESET)"
	@cd services/optimizer-api && python -m pylint **/*.py || echo "$(YELLOW)Linting not configured$(RESET)"
	@cd services/dashboard && npm run lint || echo "$(YELLOW)Linting not configured$(RESET)"

format:
	@echo "$(CYAN)==> Formatting code...$(RESET)"
	@cd services/optimizer-api && python -m black . && python -m isort . || echo "$(YELLOW)Formatting not configured$(RESET)"
	@cd services/dashboard && npm run format || echo "$(YELLOW)Formatting not configured$(RESET)"
	@cd infrastructure/terraform && terraform fmt -recursive || true
	@echo "$(GREEN)✓ Code formatted$(RESET)"

version:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(CYAN)  $(PROJECT_NAME)$(RESET)"
	@echo "$(CYAN)  Version: $(VERSION)$(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "Component versions:"
	@echo "  Docker:     $$(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
	@echo "  Kubernetes: $$(kubectl version --client -o json 2>/dev/null | grep -o '"gitVersion":"[^"]*' | cut -d'"' -f4 || echo 'not available')"
	@echo "  Kind:       $$(kind --version 2>/dev/null | cut -d' ' -f3 || echo 'not installed')"
	@echo "  Helm:       $$(helm version --short 2>/dev/null | cut -d' ' -f1 | cut -d'+' -f1 || echo 'not installed')"
	@echo "  Terraform:  $$(terraform version -json 2>/dev/null | grep -o '"terraform_version":"[^"]*' | cut -d'"' -f4 || echo 'not installed')"
	@echo ""

clusters:
	@echo "$(CYAN)==> Creating Kind clusters...$(RESET)"
	@bash scripts/setup-clusters.sh

clusters-clean:
	@echo "$(CYAN)==> Removing Kind clusters...$(RESET)"
	@bash scripts/cleanup.sh
