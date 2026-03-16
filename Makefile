# Makefile for PRism-AI

.PHONY: install dev test run-cli build-docker run-docker clean

install:
	pip install -e ".[dev]"

dev:
	uvicorn src.api.main:app --reload --port 8000

test:
	pytest tests/ --cov=src

run-cli:
	prism-ai --help

build-docker:
	docker build -t prism-ai .

run-docker:
	docker-compose up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +
	rm -rf .pytest_cache .coverage htmlcov
