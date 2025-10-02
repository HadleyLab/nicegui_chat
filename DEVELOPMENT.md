# NiceGUI Chat - Development Guide

## Project Structure

```
nicegui_chat/
├── config/
│   └── app_config.json          # Application configuration
├── prompts/
│   └── system.md                # System prompts for LLM
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration loader
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py              # Chat domain models
│   │   └── memory.py            # Memory domain models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication service
│   │   ├── memory_service.py    # Memory service
│   │   ├── agent_service.py     # AI agent service
│   │   └── chat_service.py      # Chat orchestration service
│   ├── ui/
│   │   ├── __init__.py
│   │   └── chat_ui.py           # NiceGUI chat interface
│   └── utils/
│       ├── __init__.py
│       └── exceptions.py        # Custom exceptions
├── .env                         # Environment variables (secrets)
├── .env.example                 # Environment variables template
├── .gitignore
├── main.py                      # Application entry point
├── pyproject.toml               # Project metadata
├── README.md
├── requirements.txt             # Python dependencies
├── run.py                       # Quick start script
└── run.sh                       # Shell script for quick start
```

## Architecture

### Services Layer
- **AuthService**: Manages HeySol authentication and client lifecycle
- **MemoryService**: Handles HeySol memory operations (search, add, list spaces)
- **ChatAgent**: Wraps Pydantic AI agent with DeepSeek LLM
- **ChatService**: Orchestrates chat flow with streaming responses

### Models Layer
- **Pydantic models** for type safety and validation
- **Chat models**: ConversationState, ChatMessage, MessageRole, etc.
- **Memory models**: MemoryEpisode, MemorySearchResult, MemorySpace

### UI Layer
- **NiceGUI-based** modern web interface
- **Responsive design** with Tailwind CSS classes
- **Smooth animations** and transitions
- **Real-time streaming** chat responses

## Configuration

### Environment Variables (.env)
```bash
DEEPSEEK_API_KEY=your_api_key
HEYSOL_API_KEY=your_api_key
APP_NAME=NiceGUI Chat
APP_HOST=0.0.0.0
APP_PORT=8080
```

### App Configuration (config/app_config.json)
```json
{
  "app": {...},
  "llm": {...},
  "heysol": {...},
  "chat": {...},
  "ui": {...}
}
```

## Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Development Server
```bash
python main.py
# or
python run.py
# or
bash run.sh
```

### Access the Application
Open your browser at: http://localhost:8080

## Features

### Chat Interface
- Real-time streaming responses
- Message history
- Typing indicators
- Smooth animations

### Memory Integration
- Automatic memory search before responses
- Context-aware conversations
- Memory space management

### AI Agent
- DeepSeek LLM integration
- Pydantic AI framework
- Tool calling for memory operations

## Customization

### UI Theme
Edit `config/app_config.json` under the `ui` section:
```json
{
  "ui": {
    "theme": "dark",
    "primary_color": "#6366f1",
    "background_color": "#0f172a",
    ...
  }
}
```

### System Prompt
Edit `prompts/system.md` to customize the AI behavior.

### Chat Behavior
Edit `config/app_config.json` under the `chat` section:
```json
{
  "chat": {
    "enable_memory_enrichment": true,
    "store_user_messages": true,
    "stream_chunk_size": 50,
    ...
  }
}
```
