# MammoChat™ API Documentation

This document provides detailed API documentation for the MammoChat™ application components.

## Services

### ChatService

The main orchestration service for chat operations.

#### `stream_chat(conversation, user_message, *, selected_space_ids=None, metadata=None, store_user_message=True)`

Streams AI-generated chat responses with proper state management.

**Parameters:**
- `conversation` (ConversationState): Current conversation state
- `user_message` (str): User's input message
- `selected_space_ids` (list[str], optional): Memory space filtering
- `metadata` (dict, optional): Additional context
- `store_user_message` (bool): Whether to persist user message

**Yields:**
- `ChatStreamEvent`: Streaming events for UI consumption

**Raises:**
- `AuthenticationError`: If user is not authenticated
- `ChatServiceError`: If message is empty or service fails

### AIService

Handles direct AI interactions with optional HeySol memory integration.

#### `stream_chat(message, history=None, space_ids=None)`

Streams chat responses using Pydantic AI agent or direct API fallback.

**Parameters:**
- `message` (str): User's message
- `history` (list[dict], optional): Previous conversation history
- `space_ids` (list[str], optional): HeySol space IDs to search

**Yields:**
- `str`: Response text chunks

### MemoryService

Manages HeySol memory operations.

#### `search(query, *, space_ids=None, limit=10, include_invalidated=False)`

Search memory for relevant episodes.

**Parameters:**
- `query` (str): Search query
- `space_ids` (list[str], optional): Space IDs to search in
- `limit` (int): Maximum results (default: 10)
- `include_invalidated` (bool): Include invalidated memories

**Returns:**
- `MemorySearchResult`: Search results

#### `add(message, *, space_id=None, session_id=None, source=None)`

Add a new memory episode.

**Parameters:**
- `message` (str): Memory content
- `space_id` (str, optional): Target space ID
- `session_id` (str, optional): Session identifier
- `source` (str, optional): Source attribution

**Returns:**
- `MemoryEpisode`: Created memory episode

#### `list_spaces()`

List all available memory spaces.

**Returns:**
- `list[MemorySpace]`: Available spaces

### AuthService

Simple authentication service for HeySol API access.

#### Properties

- `is_authenticated` (bool): Check if API key is available

## Data Models

### ConversationState

Represents the current conversation state.

**Attributes:**
- `conversation_id` (str): Unique conversation identifier
- `status` (ConversationStatus): Current conversation status
- `messages` (list[ChatMessage]): Conversation messages
- `execution_history` (list[ExecutionStep]): Agent execution steps
- `memory_space_ids` (list[str]): Associated memory spaces

### ChatMessage

Individual chat message model.

**Attributes:**
- `message_id` (str): Unique message identifier
- `role` (MessageRole): Message role (user/assistant/system)
- `content` (str): Message content
- `created_at` (datetime): Creation timestamp
- `metadata` (dict): Additional metadata

### Memory Models

#### MemoryEpisode

Individual memory episode.

**Attributes:**
- `episode_id` (str): Unique episode identifier
- `body` (str): Memory content
- `space_id` (str, optional): Associated space
- `created_at` (str, optional): Creation timestamp

#### MemorySearchResult

Memory search results.

**Attributes:**
- `episodes` (list[MemoryEpisode]): Found episodes
- `total` (int): Total results count

#### MemorySpace

Memory space definition.

**Attributes:**
- `space_id` (str): Unique space identifier
- `name` (str): Human-readable name
- `description` (str, optional): Space description

## Configuration

### Config

Centralized application configuration.

**Key Sections:**
- **App Info**: Name, tagline, branding
- **Server**: Host, port settings
- **AI Service**: DeepSeek configuration
- **Memory Service**: HeySol configuration
- **UI**: Theme and styling settings

### DeepSeekConfig

DeepSeek LLM configuration.

**Attributes:**
- `api_key` (str): API key
- `model` (str): Model name
- `base_url` (str): API base URL
- `system_prompt` (str): System prompt

### HeysolConfig

HeySol memory service configuration.

**Attributes:**
- `api_key` (str): API key
- `base_url` (str): Service base URL

## Error Handling

### AppError

Base exception for all application errors.

### ConfigurationError

Raised when configuration is invalid or missing.

### AuthenticationError

Raised when authentication fails.

### ChatServiceError

Raised when chat operations fail.

### MemoryServiceError

Raised when memory operations fail.

## Utilities

### Logger

Structured logging utility.

```python
from src.utils import get_logger

logger = get_logger(__name__)
logger.info("operation_completed", key="value")
```

### Static File Serving

PWA and branding asset serving utilities.

```python
from src.utils import setup_static_files

setup_static_files(app)
```

## Environment Variables

- `DEEPSEEK_API_KEY`: Required DeepSeek API key
- `HEYSOL_API_KEY`: Optional HeySol memory API key
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8080)
- `DEEPSEEK_BASE_URL`: Custom DeepSeek base URL
- `HEYSOL_BASE_URL`: Custom HeySol base URL