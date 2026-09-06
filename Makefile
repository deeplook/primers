.DEFAULT_GOAL := help

.PHONY: help format lint test catalog-check catalog-update check-all

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*## "}; {printf "  %-16s %s\n", $$1, $$2}'

format: ## Compile-check Python sources
	uv run python -m compileall scripts tests

lint: ## Compile-check Python sources quietly
	uv run python -m compileall -q scripts tests

test: ## Validate catalog.toml and run unit tests
	uv run python scripts/catalog.py validate
	uv run python -m unittest discover -s tests -v

catalog-check: ## Validate TOML and README generation
	uv run python scripts/catalog.py validate
	uv run python scripts/catalog.py check-readme

catalog-update: ## Rewrite the generated README catalog table
	uv run python scripts/catalog.py update-readme

check-all: format lint test catalog-check ## Run the safe quality gate
