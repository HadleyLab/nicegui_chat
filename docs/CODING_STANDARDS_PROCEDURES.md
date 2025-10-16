# Coding Standards and Quality Procedures

## Overview

This document provides comprehensive procedures for maintaining code quality in the NiceGUI Chat project. It integrates lean, fast coding standards with automated validation workflows to ensure consistent, high-quality code across the development team.

## 1. Complete Code Quality Workflow Procedures

### 1.1 Initial Codebase Analysis

#### Pylance Formatting Errors Detection
1. Open the project in VS Code with Pylance extension enabled
2. Review "Problems" panel for Pylance-specific formatting issues
3. Address import resolution problems and type annotation warnings
4. Fix undefined variable and missing attribute errors

#### Python Syntax Issues Resolution
```bash
# Validate Python syntax for all files
python -m py_compile src/**/*.py tests/**/*.py

# Check for import-time errors
python -c "import src; import tests"
```

#### Import Problems Resolution
1. Verify all imports resolve correctly using Pylance
2. Check for circular import issues
3. Ensure proper `__init__.py` files exist in all packages
4. Validate third-party dependencies are installed

#### Structural Deficiencies Assessment
1. Review code organization and module structure
2. Check for adherence to single responsibility principle
3. Validate async/await patterns are correctly implemented
4. Ensure proper error handling patterns are followed

### 1.2 Quality Tools Setup and Configuration

#### Tool Versions and Dependencies
```toml
# pyproject.toml - Tool Configuration
[tool.ruff]
target-version = "py313"
line-length = 88
output-format = "concise"

[tool.black]
line-length = 88
target-version = ['py313']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.13"
warn_return_any = true
disallow_untyped_defs = true
```

#### Installation Commands
```bash
# Install development dependencies
make dev-install

# Or manually
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio ruff mypy tox pre-commit
```

#### Pre-commit Hooks Setup
```bash
# Install pre-commit hooks
pre-commit install

# Update hook versions
pre-commit autoupdate
```

### 1.3 Automated Formatting Application

#### Format Command Usage
```bash
# Apply all formatting tools
make format

# Manual formatting if needed
ruff format src tests
black src tests
isort src tests
```

#### Formatting Verification
```bash
# Check if files are properly formatted
make lint

# Individual tool checks
ruff format --check src tests
black --check src tests
isort --check-only --diff src tests
```

### 1.4 Critical Linting Error Fixes

#### Ruff Configuration
```toml
[tool.ruff.lint]
select = [
    "E", "W", "F",  # Core errors and warnings
    "I", "N", "UP", "B", "C4", "PIE", "SIM", "PTH", "PL"  # Extended rules
]
ignore = [
    "PLR0913", "PLR0912", "PLR2004", "C901", "PLR0915"  # Allow explicit code patterns
]
```

#### Linting Execution
```bash
# Run linting checks
make lint

# Fix auto-fixable issues
ruff check --fix src tests

# Manual linting
ruff check src tests
```

#### Common Issues and Solutions
- **E/W**: Code style violations - auto-fix with `ruff check --fix`
- **F**: Logic errors - require manual code review and fixes
- **I**: Import organization - use `isort` to fix
- **N**: Naming conventions - rename variables/functions to match standards
- **UP**: Outdated Python syntax - update to modern patterns

### 1.5 Type Checking Error Resolution

#### MyPy Configuration
```toml
[tool.mypy]
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
strict_equality = true
show_error_codes = true
```

#### Type Checking Execution
```bash
# Run type checking
make typecheck

# Manual type checking
mypy src tests
```

#### Type Error Resolution Process
1. **Missing Type Annotations**: Add explicit type hints to function parameters and return values
2. **Any Types**: Replace `Any` with specific types where possible
3. **Optional Types**: Use `None` checks or `Optional[Type]` annotations
4. **Generic Types**: Use proper generic type annotations for collections
5. **Import Errors**: Ensure type stubs are available for third-party libraries

### 1.6 Comprehensive Verification

#### Syntax Validation
```bash
# Validate all Python files compile
python -m py_compile src/**/*.py tests/**/*.py

# Check for import errors
python -c "import sys; sys.path.insert(0, '.'); import src; import tests"
```

#### Import Testing
```bash
# Test all module imports
python -c "
import sys
sys.path.insert(0, '.')
import src.models
import src.services
import src.ui
import src.utils
import tests
print('All imports successful')
"
```

#### Quality Workflow Integration
```bash
# Run complete quality workflow
make dev

# Individual components
make test-fast    # Fast tests
make format      # Code formatting
make lint        # Linting checks
make typecheck   # Type validation
```

### 1.7 Git Commit Procedures

#### Conventional Commit Format
```bash
# Format: type(scope): description
git commit -m "feat: add user authentication service"
git commit -m "fix: resolve memory leak in chat service"
git commit -m "refactor: optimize database queries"
git commit -m "test: add integration tests for API endpoints"
git commit -m "docs: update API documentation"
```

#### Pre-commit Hook Integration
```bash
# Automatic quality checks on commit
git add .
git commit -m "feat: implement new feature"

# Pre-commit will run:
# - Code formatting (black, isort, ruff format)
# - Linting (ruff check)
# - Type checking (mypy)
# - Fast tests (pytest fast)
```

#### Quality Gate Enforcement
```bash
# Pre-push quality verification
make pre-commit

# Manual quality gate
make format && make lint && make typecheck && make test-fast
```

## 2. Maintainable Team Procedures

### 2.1 Daily Development Workflow Integration

#### Developer Onboarding
1. **Environment Setup**:
   ```bash
   make dev-install
   pre-commit install
   ```

2. **Initial Quality Check**:
   ```bash
   make dev
   ```

3. **IDE Configuration**:
   - Enable Pylance for type checking
   - Configure Black formatter
   - Set up import sorting
   - Enable Ruff linting

#### Daily Workflow
```bash
# Start of day - verify environment
make dev

# During development - regular checks
make test-fast    # After code changes
make typecheck   # Before committing

# End of day - comprehensive check
make pre-commit
```

### 2.2 Pre-commit Hook Utilization

#### Hook Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: [--line-length, "88"]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: local
    hooks:
      - id: pytest-fast
        name: Run fast tests
        entry: python run_tests.py fast
        language: system
        pass_filenames: false
        files: ^(src|tests)/.*\.py$
```

#### Hook Execution
```bash
# Manual hook execution
pre-commit run --all-files

# Run specific hooks
pre-commit run black --all-files
pre-commit run mypy --all-files

# Skip hooks if necessary (use sparingly)
SKIP=mypy,tests git commit -m "feat: temporary skip for debugging"
```

### 2.3 Code Review Quality Checklists

#### Pre-Review Checklist
- [ ] Code compiles without syntax errors
- [ ] All imports resolve correctly
- [ ] Type annotations are complete and accurate
- [ ] Code passes all linting checks
- [ ] Tests pass for the changed functionality
- [ ] No Pylance errors or warnings

#### Code Quality Review Criteria
- **Adherence to Standards**: Code follows project coding standards
- **Type Safety**: Proper type annotations and mypy compliance
- **Error Handling**: Appropriate error handling patterns
- **Performance**: No obvious performance issues
- **Test Coverage**: Tests exist for new functionality
- **Documentation**: Code is self-documenting or properly documented

#### Post-Review Actions
```bash
# After review approval
git pull origin main
make dev  # Ensure quality standards maintained
git push origin feature-branch
```

### 2.4 Continuous Integration Quality Gates

#### CI/CD Pipeline Integration
```bash
# CI quality gates (GitHub Actions)
# 1. Install dependencies
# 2. Run quality checks
# 3. Execute tests
# 4. Generate coverage reports

# Quality gate commands
make clean
make install
make lint
make typecheck
make test-ci
```

#### Quality Metrics Tracking
- **Compilation Success Rate**: 100%
- **Import Success Rate**: 100%
- **Linting Success Rate**: 100%
- **Type Check Success Rate**: 100%
- **Test Success Rate**: ≥95%
- **Coverage Threshold**: ≥70%

#### Automated Quality Enforcement
```bash
# Fail build on quality issues
#!/bin/bash
set -e  # Exit on any error

make lint        # Must pass
make typecheck   # Must pass
make test-ci     # Must pass with coverage
```

## 3. Standards Documentation Integration

### 3.1 Lean, Fast, Explicit Code Standards

This project adheres to strict coding standards defined in `.kilocode/rules/1-coding-standards.md`:

#### Core Philosophy
- **Fail Fast**: Immediate failure on invalid input
- **Minimalism**: Remove unnecessary code
- **Explicitness**: Every assumption must be explicit
- **Speed Over Robustness**: Performance-first approach

#### Code Structure Requirements
- **Single Responsibility**: Each function/class has one purpose
- **Strategic Abstractions**: Pydantic models for data flow
- **Direct Logic**: Linear code paths with NiceGUI patterns

#### Error Handling Standards
- **No Try-Catch**: Exceptions for unrecoverable errors only
- **Validation at Entry**: Pydantic model validation
- **No Fallbacks**: Fail immediately, no alternative paths

### 3.2 Automated Validation Standards

Comprehensive quality validation as defined in `.kilocode/rules/4-comprehensive-code-quality.md`:

#### Zero Tolerance Policy
- **Syntax Validation**: All Python files must compile
- **Import Testing**: All modules must import successfully
- **Standards Compliance**: Full PEP 8, 257, 484 adherence
- **Automated Enforcement**: Industry-standard tools only

#### Quality Tools Stack
- **mypy**: Static type checking with strict settings
- **ruff**: Fast linting with comprehensive rule set
- **black**: Uncompromising code formatting
- **isort**: Import organization and sorting

## 4. Troubleshooting and Maintenance

### 4.1 Common Issues and Solutions

#### Import Resolution Problems
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Verify package structure
find src -name "__init__.py" | sort

# Test individual imports
python -c "import src.models.chat; print('Import successful')"
```

#### Type Checking Issues
```bash
# Run mypy with verbose output
mypy src --show-error-codes --show-traceback

# Check for missing type stubs
python -c "import mypy.api; print('mypy available')"
```

#### Pre-commit Hook Failures
```bash
# Debug hook execution
pre-commit run --verbose <hook-id>

# Skip problematic hooks temporarily
SKIP=<hook-id> git commit

# Update hook versions
pre-commit autoupdate
```

### 4.2 Quality Metrics Monitoring

#### Regular Quality Audits
```bash
# Weekly quality assessment
make dev
make coverage

# Monthly comprehensive review
make clean
make install
make test-all
make coverage
```

#### Performance Benchmarking
```bash
# Track quality check performance
time make lint
time make typecheck
time make test-fast

# Monitor for regressions
# Store timing results and alert on significant slowdowns
```

## 5. Appendices

### 5.1 Quick Reference Commands

```bash
# Development workflow
make dev-install     # Setup environment
make dev            # Full quality check
make pre-commit     # Pre-commit validation

# Individual tools
make format         # Code formatting
make lint          # Linting checks
make typecheck     # Type validation
make test-fast     # Fast tests

# Maintenance
make clean         # Clean artifacts
make coverage      # Generate coverage
```

### 5.2 Configuration Files Reference

- **`pyproject.toml`**: Tool configurations and dependencies
- **`Makefile`**: Quality workflow commands
- **`.pre-commit-config.yaml`**: Pre-commit hook definitions
- **`requirements.txt`**: Runtime and development dependencies

### 5.3 Standards Compliance Checklist

- [ ] Code compiles without syntax errors
- [ ] All imports resolve successfully
- [ ] Type annotations are complete and correct
- [ ] Code passes all linting rules (E, W, F levels)
- [ ] Code is properly formatted (black, isort)
- [ ] Tests pass for all new functionality
- [ ] No Pylance errors or warnings
- [ ] Follows lean, fast, explicit coding standards
- [ ] Commits use conventional commit format

---

**Last Updated**: October 2025
**Version**: 1.0.0
**Maintainer**: Development Team

This document serves as the authoritative guide for code quality procedures and must be followed by all team members to ensure consistent, high-quality code delivery.