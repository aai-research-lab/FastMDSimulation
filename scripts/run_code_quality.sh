# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check code style with Flake8
flake8 src/ tests/ --max-line-length=130

# Run type checking with mypy
#mypy src/

# Run tests with coverage
pytest tests/ --cov=fastmdsimulation --cov-report=term-missing

# Or run everything in one command
#black src/ tests/ && isort src/ tests/ && flake8 src/ tests/ && mypy src/ && pytest tests/ --#cov=fastmdsimulation