.PHONY: help format lint test

default: help

help: ## Show this help message
	@echo "Usage: make <target>"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

format: ## Format source code
	@echo "Format with ruff"
	@uv run -- ruff format .

lint: ## Check source code with linters
	@echo "Lint with ruff"
	@uv run -- ruff check . --fix

	@echo "Lint with ty"
	@uv run -- ty check .

# 	@echo "Lint with mypy"
# 	@uv run -- mypy .

test: ## Test with pytest
	@echo "Testing with pytest"
	@uv run -- pytest . --cov
