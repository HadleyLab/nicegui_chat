# MammoChat™ Testing Framework
# Lean and agile development testing commands

.PHONY: help test test-fast test-all test-integration test-ci test-models test-services test-bugs coverage lint typecheck clean install dev-install

# Default target
help:
	@echo "MammoChat™ Testing Framework"
	@echo ""
	@echo "Available commands:"
	@echo "  make test-fast      - Run fast unit tests (no coverage)"
	@echo "  make test-all       - Run all tests with coverage"
	@echo "  make test-integration - Run integration tests with real APIs"
	@echo "  make test-ci        - Run CI-style tests with coverage"
	@echo "  make test-models    - Run model tests only"
	@echo "  make test-services  - Run service tests only"
	@echo "  make test-bugs      - Run bug-specific tests"
	@echo "  make coverage       - Generate coverage report"
	@echo "  make lint           - Run linting checks"
	@echo "  make typecheck      - Run type checking"
	@echo "  make clean          - Clean test artifacts"
	@echo "  make install        - Install dependencies"
	@echo "  make dev-install    - Install development dependencies"

# Testing commands
test-fast:
	python run_tests.py fast

test-all:
	python run_tests.py all

test-integration:
	python run_tests.py integration

test-ci:
	python run_tests.py ci

test-models:
	python run_tests.py models

test-services:
	python run_tests.py services

test-bugs:
	python run_tests.py bugs

coverage:
	python run_tests.py coverage

# Quality checks
lint:
	ruff check src tests
	ruff format --check src tests

typecheck:
	mypy src tests

# Maintenance
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf junit.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install:
	pip install -r requirements.txt

dev-install: install
	pip install pytest pytest-cov pytest-asyncio ruff mypy tox

# Tox environments
tox-test:
	tox -e py313

tox-lint:
	tox -e lint

tox-typecheck:
	tox -e typecheck

tox-fast:
	tox -e fast

tox-integration:
	tox -e integration

# CI/CD ready
ci: clean install
	pytest --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=70 --junitxml=junit.xml

# Development workflow
dev: test-fast lint typecheck

# Pre-commit style checks
pre-commit: lint typecheck test-fast