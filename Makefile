# TellCo User Analytics — development commands
# Run `make` or `make help` to list targets.

.DEFAULT_GOAL := help

PYTHON   ?= python3
VENV     := .venv
BIN      := $(VENV)/bin
PIP      := $(BIN)/pip
PYTEST   := $(BIN)/pytest
RUFF     := $(BIN)/ruff
PACKAGE  := tellco_user_analytics

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help message
	@echo "TellCo User Analytics — available targets:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

.PHONY: venv
venv: ## Create virtual environment (.venv)
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@echo "Virtual environment ready: $(VENV)"
	@echo "Activate with: source $(VENV)/bin/activate"

.PHONY: install
install: venv ## Install package (runtime dependencies only)
	$(PIP) install --upgrade pip
	$(PIP) install -e .

.PHONY: install-dev
install-dev: venv ## Install package + dev tools (pytest, ruff, jupyter)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

.PHONY: env
env: ## Copy .env.example to .env if missing
	@test -f .env || cp .env.example .env
	@echo ".env ready — edit credentials if needed."

# ---------------------------------------------------------------------------
# Quality checks (mirrors .github/workflows/ci.yml)
# ---------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ruff linter
	$(RUFF) check src tests app

.PHONY: format
format: ## Auto-format code with ruff
	$(RUFF) format src tests app
	$(RUFF) check src tests app --fix

.PHONY: format-check
format-check: ## Verify formatting without writing changes
	$(RUFF) format --check src tests app

.PHONY: test
test: ## Run unit tests
	$(PYTEST) tests/ -v --tb=short

.PHONY: ci
ci: lint format-check test ## Run full CI suite locally (lint + format + test)

# ---------------------------------------------------------------------------
# Database (Docker PostgreSQL)
# ---------------------------------------------------------------------------

.PHONY: db-up
db-up: ## Start PostgreSQL container
	docker compose up -d

.PHONY: db-down
db-down: ## Stop PostgreSQL container (keeps data)
	docker compose down

.PHONY: db-reset
db-reset: ## Stop PostgreSQL and delete all data volumes
	docker compose down -v

.PHONY: db-load
db-load: ## Start DB and load telecom.sql (skips if already loaded)
	@chmod +x scripts/load_database.sh
	./scripts/load_database.sh

.PHONY: db-verify
db-verify: ## Print xdr_data row count from PostgreSQL
	@$(BIN)/python -c "from $(PACKAGE).db.connection import verify_connection; print('Rows:', verify_connection())"

.PHONY: db-psql
db-psql: ## Open interactive psql shell in the container
	docker compose exec postgres psql -U postgres -d tellco

.PHONY: mysql-up
mysql-up: ## Start MySQL container (satisfaction export)
	docker compose up -d mysql

.PHONY: mysql-verify
mysql-verify: ## Sample rows from MySQL satisfaction table
	@$(BIN)/python -c "from $(PACKAGE).db.mysql_export import verify_mysql_export; print(verify_mysql_export())"

.PHONY: mlflow-ui
mlflow-ui: ## Launch MLflow UI at http://127.0.0.1:5000
	$(BIN)/mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000

# ---------------------------------------------------------------------------
# Notebooks & one-shot setup
# ---------------------------------------------------------------------------

.PHONY: notebook
notebook: ## Launch Jupyter from the notebooks/ directory
	@cd notebooks && $(BIN)/jupyter notebook

.PHONY: dashboard
dashboard: install-dev ## Launch Streamlit dashboard at http://127.0.0.1:8501
	$(BIN)/pip install -q -e ".[dashboard]"
	$(BIN)/streamlit run app/Home.py --server.port 8501

.PHONY: dashboard-docker
dashboard-docker: ## Build and run dashboard via Docker Compose (requires db-load first)
	docker compose up -d postgres mysql
	docker compose build dashboard
	docker compose up -d dashboard
	@echo "Dashboard → http://127.0.0.1:8501"

.PHONY: docker-build
docker-build: ## Build dashboard Docker image locally
	docker build -t tellco-dashboard:latest .

.PHONY: feature-store-init
feature-store-init: ## Create PostgreSQL feature_store schema
	@$(BIN)/python -c "from $(PACKAGE).db.feature_store import init_feature_store; init_feature_store(); print('feature_store schema ready')"

.PHONY: setup
setup: install-dev env db-load ## Full first-time setup (venv, deps, .env, database)
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  source $(VENV)/bin/activate"
	@echo "  make test"
	@echo "  make notebook"

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

.PHONY: clean
clean: ## Remove caches and build artefacts
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned caches and egg-info."

.PHONY: clean-all
clean-all: clean db-reset ## Remove caches and wipe database volumes
	rm -rf $(VENV)
	@echo "Removed virtual environment and database volumes."
