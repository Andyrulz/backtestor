# Makefile for Kite Trading System

.PHONY: help install test lint format run clean

# Default target
help:
	@echo "Available commands:"
	@echo "  install    Install dependencies"
	@echo "  test       Run tests"
	@echo "  lint       Run code linting"
	@echo "  format     Format code"
	@echo "  run        Run the Streamlit app"
	@echo "  clean      Clean up generated files"

install:
	pip install -r requirements.txt

test:
	pytest -v

lint:
	flake8 src/ tests/

format:
	black src/ tests/

run:
	streamlit run src/app.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/
