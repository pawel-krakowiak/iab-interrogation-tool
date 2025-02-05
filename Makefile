# 🛡️

# Define the project root directory
PROJECT_ROOT := $(shell pwd)

# Define the source directory
SRC_DIR := $(PROJECT_ROOT)/src

# Define the test directory
TEST_DIR := $(PROJECT_ROOT)/tests

# Define the Python executable
PYTHON := python3

# Define the pytest executable
PYTEST := poetry run pytest

.PHONY: all test run lint format install

# Default target
all: install lint test run

# Target to install dependencies
install:
	@echo "🚨 Installing dependencies..."
	@poetry install

# Target to run tests
test:
	@echo "🔍 Running tests..."
	PYTHONPATH=$(PROJECT_ROOT) poetry run $(PYTEST) $(TEST_DIR)

# Target to run the application
run:
	@echo "🚔 Running application..."
	PYTHONPATH=$(PROJECT_ROOT) poetry run $(PYTHON) $(SRC_DIR)/views/main_window.py

# Target to run linters
lint:
	@echo "🔍 Running linters..."
	PYTHONPATH=$(PROJECT_ROOT) poetry run flake8 --config=$(PROJECT_ROOT)/.flake8 $(SRC_DIR) $(TEST_DIR)
	PYTHONPATH=$(SRC_DIR) poetry run mypy --config=$(PROJECT_ROOT)/pyproject.toml $(SRC_DIR)

# Target to format code
format:
	@echo "🛠️ Formatting code..."
	@poetry run black $(SRC_DIR) $(TEST_DIR)

lud:
	@echo 'robi lud'