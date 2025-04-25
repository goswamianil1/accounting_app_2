#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Run Black for code formatting
echo "Running Black formatter..."
black .

# Run Flake8 for linting
echo "Running Flake8 linter..."
flake8 .

# Deactivate virtual environment
deactivate

echo "Formatting and linting complete!" 