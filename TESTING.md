# MammoChat™ Testing Framework

A comprehensive testing framework designed for lean and agile development, achieving **77% code coverage** with real API integration.

## Overview

This testing framework follows the coding standards:
- **Fail Fast**: Tests fail immediately on any deviation
- **Minimalism**: Focused test cases without unnecessary code
- **Explicitness**: Clear test names and comprehensive assertions
- **Integration over Mocking**: Real API calls when credentials available
- **Speed First**: Fast unit tests, minimal overhead

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Tests
```bash
# Fast unit tests (recommended for development)
make test-fast
# or
python run_tests.py fast

# All tests with coverage
make test-all
# or
python run_tests.py all

# Integration tests with real APIs
make test-integration
# or
python run_tests.py integration
```

## Test Categories

### Unit Tests (`pytest -m "not integration"`)
- **Models**: Pydantic validation, business logic
- **Services**: Core business logic with mocking
- **Utilities**: Helper functions and utilities
- **Bugs**: Specific regression tests

### Integration Tests (`pytest -m integration`)
- **Real API Calls**: DeepSeek and HeySol APIs
- **End-to-End Flows**: Complete chat interactions
- **Live Validation**: Actual service integrations

### Coverage
- **77% overall coverage** with real API keys
- **100% coverage** for core business logic
- **Real API integration** for complex async operations

## Testing Commands

### Development Workflow
```bash
# Quick development checks
make dev          # fast tests + lint + typecheck

# Pre-commit checks
make pre-commit   # all quality gates

# CI simulation
make ci           # full CI pipeline
```

### Specific Test Suites
```bash
# Test specific components
make test-models      # Model tests only
make test-services    # Service tests only
make test-bugs        # Bug regression tests

# Coverage reports
make coverage         # Generate HTML coverage report
python run_tests.py coverage  # Open htmlcov/index.html
```

### Quality Gates
```bash
# Linting and formatting
make lint            # ruff check and format

# Type checking
make typecheck       # mypy static analysis

# Clean artifacts
make clean           # Remove test artifacts
```

## Configuration

### pytest.ini
- Coverage thresholds (70% minimum)
- Test markers (unit, integration, e2e)
- Async testing configuration
- HTML and XML reporting

### .coveragerc
- Source directory configuration
- Exclusion patterns
- Report formatting

### tox.ini
- Multi-environment testing
- Quality checks (lint, typecheck)
- CI/CD integration

## CI/CD Integration

### GitHub Actions
- **Multi-Python testing**: 3.11, 3.12, 3.13
- **Quality gates**: lint, format, typecheck
- **Coverage reporting**: Codecov integration
- **Integration tests**: Real API validation on main/feature branches

### Pre-commit Hooks
- **Automatic quality checks** on commit
- **ruff** linting and formatting
- **mypy** type checking
- **Fast test runs** for regression prevention

## API Keys for Integration Tests

Integration tests require real API keys:

```bash
# Set environment variables
export DEEPSEEK_API_KEY="your_key_here"
export HEYSOL_API_KEY="your_key_here"

# Or create .env file
echo "DEEPSEEK_API_KEY=your_key" > .env
echo "HEYSOL_API_KEY=your_key" >> .env
```

Tests automatically skip if keys are not available.

## Test Structure

```
tests/
├── test_models.py      # Pydantic models and validation
├── test_services.py    # Business logic services
├── test_utils.py       # Utility functions
├── test_integration.py # Real API integration tests
├── test_bugs.py        # Bug regression tests
├── test_ui.py          # UI component tests (future)
└── test_e2e.py         # End-to-end tests (future)
```

## Coverage Goals

- **Unit Tests**: 100% coverage for core business logic
- **Integration Tests**: Real API validation where possible
- **Overall Target**: 75%+ coverage with real APIs
- **Quality over Quantity**: Meaningful tests over artificial coverage

## Performance

- **Fast unit tests**: < 30 seconds for core tests
- **Integration tests**: < 5 minutes with real APIs
- **CI pipeline**: < 10 minutes total
- **Incremental testing**: Fast feedback loops

## Best Practices

### Writing Tests
- **Descriptive names**: `test_user_creation_success`
- **Single responsibility**: One assertion per test
- **Arrange-Act-Assert**: Clear test structure
- **Real APIs preferred**: Integration over mocking

### Markers
```python
@pytest.mark.integration  # Requires real APIs
@pytest.mark.slow         # Long-running tests
@pytest.mark.unit         # Unit tests (default)
```

### Fixtures
- **Reusable setup**: Common test data
- **Dependency injection**: Mock services
- **Cleanup**: Proper resource management

## Troubleshooting

### Common Issues
- **API keys missing**: Integration tests skip automatically
- **Coverage low**: Check .coveragerc exclusions
- **Slow tests**: Use `pytest -x` to stop on first failure

### Debug Commands
```bash
# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show coverage details
pytest --cov-report=term-missing

# Run specific test
pytest tests/test_models.py::TestChatMessage::test_create_user_message
```

## Contributing

1. **Write tests first** (TDD approach)
2. **Run fast tests** during development
3. **Add integration tests** for new API features
4. **Update coverage** as code evolves
5. **Follow naming conventions** and markers

## Metrics

- **Test Count**: 106 tests
- **Coverage**: 77% with real APIs
- **CI Time**: < 10 minutes
- **Quality Gates**: ruff, mypy, pytest

This framework enables confident, agile development with comprehensive test coverage and real-world validation.