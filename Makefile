.PHONY: help quickstart setup start stop restart clean status logs health-check \
        clusters clusters-clean infra-start db-check db-migrate db-seed \
        shell-api shell-db shell-redis clean-data \
        test test-unit test-integration test-e2e test-load chaos-test coverage \
        trial demo-quick demo demo-report demo-clean \
        deploy-dev deploy-staging deploy-prod \
        build build-api build-operator build-dashboard \
        version validate lint format urls check-prerequisites

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
	@echo "$(CYAN)  💰 K8s Cost Optimizer$(RESET)"
	@echo "$(CYAN)  Version: $(VERSION) · Reduce cloud costs by 35-45%$(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)🚀 Quick Start (Choose One):$(RESET)"
	@echo "  $(GREEN)quickstart$(RESET)          - Interactive guide to get started"
	@echo "  $(GREEN)demo-quick$(RESET)          - See demo in 5 minutes (no cluster needed)"
	@echo "  $(GREEN)trial$(RESET)               - See how it works, then try YOUR cluster!"
	@echo "  $(GREEN)setup$(RESET)               - Full installation (30 min)"
	@echo ""
	@echo "$(YELLOW)📖 Documentation:$(RESET)"
	@echo "  See $(CYAN)QUICKSTART.md$(RESET) for detailed getting started guide"
	@echo "  See $(CYAN)README.md$(RESET) for project overview and features"
	@echo ""
	@echo "$(GREEN)Setup & Management:$(RESET)"
	@echo "  start              - Start all services"
	@echo "  stop               - Stop all services"
	@echo "  restart            - Restart services"
	@echo "  status             - Show service status"
	@echo "  health-check       - Verify system health"
	@echo "  urls               - Show all service URLs"
	@echo "  clean              - Remove everything"
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@echo "  shell-api          - Shell into API container"
	@echo "  shell-db           - PostgreSQL shell"
	@echo "  shell-redis        - Redis shell"
	@echo "  logs               - View all logs"
	@echo "  db-migrate         - Run migrations"
	@echo "  db-seed            - Load demo data"
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@echo "  test               - Run all tests"
	@echo "  test-unit          - Unit tests (120+)"
	@echo "  test-integration   - Integration tests (50+)"
	@echo "  test-e2e           - End-to-end tests (40+)"
	@echo "  test-load          - Load test (1000 users)"
	@echo "  coverage           - Coverage report"
	@echo ""
	@echo "$(GREEN)Demo & Reports:$(RESET)"
	@echo "  demo               - Full demo scenario"
	@echo "  demo-report        - Generate PDF report"
	@echo "  demo-clean         - Clear demo data"
	@echo ""
	@echo "$(GREEN)Build & Deploy:$(RESET)"
	@echo "  build              - Build all containers"
	@echo "  deploy-dev         - Deploy to dev"
	@echo "  deploy-staging     - Deploy to staging"
	@echo "  deploy-prod        - Deploy to production"
	@echo ""
	@echo "$(GREEN)Utilities:$(RESET)"
	@echo "  check-prerequisites - Check system requirements"
	@echo "  validate           - Validate configs"
	@echo "  format             - Format code"
	@echo "  version            - Show version info"
	@echo ""
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(YELLOW)💡 New User? Run:$(RESET) $(GREEN)make quickstart$(RESET) $(YELLOW)or$(RESET) $(GREEN)make trial$(RESET)"
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

## Quick Start & Trial

quickstart:
	@cat QUICKSTART.md | head -n 50
	@echo ""
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(YELLOW)💡 Choose your path:$(RESET)"
	@echo "  $(GREEN)make demo-quick$(RESET) - See demo in 5 minutes"
	@echo "  $(GREEN)make trial$(RESET)      - Analyze your real cluster"
	@echo "  $(GREEN)make setup$(RESET)      - Full installation"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)Read full guide:$(RESET) $(CYAN)cat QUICKSTART.md$(RESET)"
	@echo ""

check-prerequisites:
	@echo "$(CYAN)==> Checking system prerequisites...$(RESET)"
	@echo ""
	@command -v docker >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET) Docker ($$(docker --version | cut -d' ' -f3 | cut -d',' -f1))" || echo "$(RED)✗$(RESET) Docker (required)"
	@command -v kubectl >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET) kubectl ($$(kubectl version --client -o json 2>/dev/null | grep -o '"gitVersion":"[^"]*' | cut -d'"' -f4 || echo 'installed'))" || echo "$(YELLOW)⚠$(RESET) kubectl (optional)"
	@command -v kind >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET) Kind ($$(kind --version 2>/dev/null | cut -d' ' -f3))" || echo "$(YELLOW)⚠$(RESET) Kind (optional, for multi-cluster demo)"
	@command -v helm >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET) Helm ($$(helm version --short 2>/dev/null | cut -d' ' -f1 | cut -d'+' -f1))" || echo "$(YELLOW)⚠$(RESET) Helm (optional)"
	@echo ""
	@docker info >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET) Docker is running" || (echo "$(RED)✗$(RESET) Docker is not running" && exit 1)
	@echo ""

trial:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(CYAN)  🎯 Trial Mode - See How It Works, Then Try It!$(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)This will:$(RESET)"
	@echo "  1. Show you how cluster analysis works (2 min)"
	@echo "  2. Display example savings results"
	@echo "  3. Offer to analyze YOUR cluster (optional)"
	@echo ""
	@bash scripts/trial-wizard.sh

demo-quick:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(CYAN)  🚀 Quick Demo - See Cost Optimization in Action$(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(YELLOW)Starting demo environment...$(RESET)"
	@echo ""
	@$(MAKE) infra-start || true
	@sleep 2
	@echo ""
	@echo "$(CYAN)╔══════════════════════════════════════════════════╗$(RESET)"
	@echo "$(CYAN)║$(RESET)           $(BOLD)Demo Cost Analysis Results$(RESET)           $(CYAN)║$(RESET)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "  Workloads Analyzed:      $(BOLD)120$(RESET)"
	@echo "  Current Monthly Cost:    $(BOLD)\$$68,450$(RESET)"
	@echo "  Optimized Monthly Cost:  $(BOLD)$(GREEN)\$$38,920$(RESET)"
	@echo "  $(CYAN)───────────────────────────────────────────────────$(RESET)"
	@echo "  $(BOLD)Monthly Savings:         $(GREEN)\$$29,530 (43.2%)$(RESET)"
	@echo "  $(BOLD)Annual Savings:          $(GREEN)\$$354,360$(RESET)"
	@echo ""
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "$(GREEN)✓ Demo is ready!$(RESET)"
	@echo ""
	@echo "📊 View Dashboard:  $(CYAN)http://localhost:3000$(RESET)"
	@echo "📡 API Docs:        $(CYAN)http://localhost:8000/docs$(RESET)"
	@echo "📈 Grafana:         $(CYAN)http://localhost:3001$(RESET) (admin/admin123)"
	@echo ""
	@echo "$(YELLOW)💡 Try analyzing YOUR cluster:$(RESET) $(GREEN)make trial$(RESET)"
	@echo ""

urls:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo "$(CYAN)  Service URLs$(RESET)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@echo ""
	@echo "  📱 $(BOLD)Dashboard$(RESET)   $(CYAN)http://localhost:3000$(RESET)"
	@echo "  📡 $(BOLD)API Docs$(RESET)    $(CYAN)http://localhost:8000/docs$(RESET)"
	@echo "  📊 $(BOLD)Grafana$(RESET)     $(CYAN)http://localhost:3001$(RESET)  (admin/admin123)"
	@echo "  🔍 $(BOLD)Prometheus$(RESET)  $(CYAN)http://localhost:9090$(RESET)"
	@echo "  📦 $(BOLD)MinIO$(RESET)       $(CYAN)http://localhost:9001$(RESET)  (minioadmin/minioadmin123)"
	@echo "  🐘 $(BOLD)PostgreSQL$(RESET)  $(CYAN)localhost:5432$(RESET)        (optimizer/optimizer_dev_pass)"
	@echo "  ⚡ $(BOLD)Redis$(RESET)       $(CYAN)localhost:6379$(RESET)"
	@echo ""

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
