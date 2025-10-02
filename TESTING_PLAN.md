# Comprehensive Testing Plan for MammoChat

## Overview
This document outlines a comprehensive testing strategy for the MammoChat application to achieve >90% code coverage while following the coding standards defined in `.kilocode/rules`.

## Testing Principles
- **Unit Tests Primary**: Test individual functions in isolation
- **Integration Tests for APIs**: Use real API keys and live calls for external API validation
- **Fail Tests**: Tests must fail on any deviation from expected behavior
- **Speed First**: Optimize tests for performance, minimal overhead
- **Explicit Coverage**: Ensure all code paths are tested

## Infrastructure Setup

### 1. Git Configuration
- Add `.kilocode` directory to `.gitignore` to exclude AI assistant configuration

### 2. Testing Dependencies
Update `pyproject.toml` with comprehensive testing tools:
```toml
[project.optional-dependencies]
dev = [
  "pytest>=7.4",
  "pytest-asyncio>=0.23",
  "pytest-cov>=4.1",
  "black>=23.0",
  "ruff>=0.1.0",
  "mypy>=1.8",
  "isort>=5.12",
]
```

### 3. Test Configuration
Create `pytest.ini` with coverage settings:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=90
asyncio_mode = auto
```

## Test Structure

### Directory Layout
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_config.py
│   ├── test_models_chat.py
│   ├── test_models_memory.py
│   ├── test_exceptions.py
│   ├── test_services_auth.py
│   ├── test_services_memory.py
│   ├── test_services_chat.py
│   ├── test_services_agent.py
│   └── test_ui_chat.py
└── integration/             # Integration tests
    ├── test_api_auth.py
    ├── test_api_memory.py
    └── test_api_chat.py
```

### Shared Fixtures (`conftest.py`)
- Mock configuration data
- Test database setup (if needed)
- API client mocks for unit tests
- Environment variable management

## Unit Test Coverage Plan

### 1. Configuration Module (`src/config.py`)
**Coverage Targets:**
- PromptStore lazy loading and caching
- All dataclass validation and creation
- Environment variable loading
- JSON configuration parsing
- Error handling for missing/invalid config

**Test Cases:**
- Valid configuration loading
- Missing configuration file
- Invalid JSON structure
- Environment variable precedence
- Prompt file loading and caching
- Dataclass validation errors

### 2. Chat Models (`src/models/chat.py`)
**Coverage Targets:**
- All Pydantic model validation
- Enum usage and serialization
- Conversation state management
- Message appending and retrieval

**Test Cases:**
- ChatMessage creation and validation
- ConversationState operations
- ExecutionStep creation
- ChatStreamEvent serialization
- Edge cases (empty messages, invalid roles)

### 3. Memory Models (`src/models/memory.py`)
**Coverage Targets:**
- API response parsing
- Model validation
- Factory methods

**Test Cases:**
- MemoryEpisode creation from API data
- MemorySearchResult parsing
- MemorySpace creation
- Invalid API response handling

### 4. Exceptions (`src/utils/exceptions.py`)
**Coverage Targets:**
- Exception hierarchy
- Error message formatting

**Test Cases:**
- Exception instantiation
- Inheritance verification
- Error message content

### 5. Authentication Service (`src/services/auth_service.py`)
**Coverage Targets:**
- Client initialization with/without API key
- Authentication state management
- Header generation
- Error handling for failed initialization

**Test Cases:**
- Successful authentication
- Failed authentication (invalid key)
- Logout functionality
- Header generation
- Client property access

### 6. Memory Service (`src/services/memory_service.py`)
**Coverage Targets:**
- Search operation with various parameters
- Memory addition
- Space listing
- Authentication requirement enforcement
- Error handling

**Test Cases:**
- Successful search operations
- Memory addition
- Space listing
- Authentication errors
- API response parsing errors

### 7. Chat Service (`src/services/chat_service.py`)
**Coverage Targets:**
- Stream chat functionality
- Message validation
- Conversation state updates
- Chunking logic
- Error handling

**Test Cases:**
- Valid chat streaming
- Empty message rejection
- Authentication requirement
- Conversation state management
- Error propagation

### 8. Agent Service (`src/services/agent_service.py`)
**Coverage Targets:**
- Agent initialization
- Tool registration
- Response generation
- System prompt building
- Error handling

**Test Cases:**
- Agent creation with valid config
- Tool execution (memory search/ingest)
- Response generation
- Invalid configuration handling
- System prompt construction

### 9. Chat UI (`src/ui/chat_ui.py`)
**Coverage Targets:**
- UI component creation
- Event handling
- State management
- Dark mode toggling
- Message display logic

**Test Cases:**
- UI initialization
- Message sending
- Conversation management
- Dark mode toggle
- Error display
- Component state changes

## Integration Test Coverage Plan

### API Integration Tests
**Coverage Targets:**
- Real API calls with test credentials
- End-to-end service interactions
- Authentication workflows
- Memory operations
- Chat streaming

**Test Cases:**
- Full authentication flow
- Memory search and storage
- Chat conversation flow
- Error scenarios with real APIs
- Rate limiting and quota handling

## Coverage Analysis Strategy

### Coverage Metrics
- **Line Coverage**: >90%
- **Branch Coverage**: >85%
- **Function Coverage**: >95%
- **Statement Coverage**: >90%

### Coverage Exclusions
- Test files themselves
- Debug-only code
- Library compatibility shims
- Error handling for unsupported platforms

### Coverage Reporting
- HTML reports for detailed analysis
- Terminal output for CI/CD
- Coverage badges for documentation
- Trend analysis over time

## Code Quality Integration

### Automated Quality Checks
1. **Syntax Validation**: `python -m py_compile` on all files
2. **Import Testing**: Verify all imports work
3. **Type Checking**: `mypy` validation
4. **Linting**: `ruff` for style and errors
5. **Formatting**: `black` and `isort` for consistency

### Quality Gates
- All Python files must compile without syntax errors
- All modules must import successfully
- 100% mypy compliance
- Zero critical ruff errors
- 100% black formatting compliance
- 100% isort organization

## Implementation Phases

### Phase 1: Infrastructure Setup
1. Update .gitignore
2. Install testing dependencies
3. Configure pytest and coverage
4. Create test directory structure

### Phase 2: Unit Test Development
1. Create shared fixtures
2. Implement model tests
3. Implement service tests
4. Implement UI tests

### Phase 3: Integration Testing
1. Set up test API credentials
2. Implement API integration tests
3. Test end-to-end workflows

### Phase 4: Coverage Optimization
1. Run initial coverage analysis
2. Identify coverage gaps
3. Add missing test cases
4. Optimize test performance

### Phase 5: Quality Assurance
1. Apply code quality tools
2. Fix identified issues
3. Validate all quality gates
4. Final coverage verification

## Success Criteria
- ✅ >90% code coverage achieved
- ✅ All tests pass consistently
- ✅ Code quality standards met
- ✅ No critical linting errors
- ✅ Type checking passes
- ✅ All imports successful
- ✅ Documentation updated

## Maintenance Strategy
- Run tests on every commit
- Update tests with code changes
- Monitor coverage trends
- Regular dependency updates
- Performance regression testing