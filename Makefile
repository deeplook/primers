.DEFAULT_GOAL := help

.PHONY: help format lint test check-all

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*## "}; {printf "  %-16s %s\n", $$1, $$2}'

format: ## Compile-check Python sources
	uv run python -m compileall scripts tests

lint: ## Compile-check Python sources quietly
	uv run python -m compileall -q scripts tests

test: ## Validate catalog.toml and run unit tests
	uv run python scripts/catalog.py validate
	uv run python -m unittest -v

check-all: format lint test ## Run the safe quality gate
