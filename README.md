# MammoChat™ 💗

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A compassionate AI companion dedicated to supporting breast cancer patients on their healthcare journey. MammoChat™ helps patients find clinical trials, navigate treatment options, access peer support, and make informed healthcare decisions.

## Features

### 🔬 Clinical Trial Matching
- Connect patients with relevant clinical trials that match their specific diagnosis, treatment history, and preferences
- Intelligent search across trial databases using patient-specific criteria

### 💊 Treatment Navigation
- Provide clear, empathetic guidance about treatment paths and healthcare decisions
- Explain complex medical information in accessible, non-technical language

### 👥 Peer Support Connection
- Facilitate connections with supportive communities of patients who understand their experience
- Help patients find local support groups and online communities

### 💪 Decision Empowerment
- Support patients in feeling confident and informed about their healthcare choices
- Provide personalized guidance based on their unique journey and preferences

## Architecture

MammoChat™ follows a layered architecture with clear separation of concerns:

- **Configuration Management** (`config.py`) - Centralized settings and environment variables
- **Business Logic** (`src/services/`) - AI interactions, chat orchestration, memory management
- **User Interface** (`src/ui/`) - Web-based chat interface using NiceGUI
- **Data Models** (`src/models/`) - Pydantic models for type safety
- **Utilities** (`src/utils/`) - Shared utilities and error handling

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mammochat.git
cd mammochat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `DEEPSEEK_API_KEY` - Your DeepSeek API key
- `HEYSOL_API_KEY` - Your HeySol memory API key (optional)

## Usage

### Running the Application

```bash
python main.py
```

The application will start on `http://localhost:8080` (configurable in `config/app.json`).

### Configuration

- **App Settings**: `config/app.json` - Application metadata, branding, server config
- **Theme**: `config/scene.json` - UI colors, styling, and branding
- **System Prompt**: `config/system.md` - AI behavior and capabilities

## Memory-First Approach

MammoChat™ uses a memory-first approach to provide personalized, contextual support:

1. **Memory Check First** - Always searches patient memory before any other actions
2. **Contextual Responses** - Uses conversation history and preferences for personalized support
3. **Continuous Learning** - Stores useful information in memory for future interactions

## API Documentation

### Chat Service

The core chat functionality is provided through the `ChatService` class:

```python
from src.services.chat_service import ChatService

chat_service = ChatService(auth_service, memory_service, config)
response = await chat_service.stream_chat(conversation, user_message)
```

### AI Service

Direct AI interactions via the `AIService` class:

```python
from src.services.ai_service import AIService

ai_service = AIService()
response = await ai_service.stream_chat(message, history)
```

### Memory Service

Persistent memory management:

```python
from src.services.memory_service import MemoryService

memory_service = MemoryService(auth_service)
result = await memory_service.search(query, space_ids)
```

## Development

### Code Quality

The project maintains high code quality standards:

- **Linting**: `ruff` for fast Python linting
- **Formatting**: `black` for consistent code formatting
- **Import Sorting**: `isort` for organized imports
- **Type Checking**: `mypy` for static type analysis

Run quality checks:
```bash
ruff check .
black .
isort .
mypy .
```

### Testing

```bash
pytest
```

### Project Structure

```
mammochat/
├── config/                 # Configuration files
│   ├── app.json           # Application settings
│   ├── scene.json         # UI theme and branding
│   └── system.md          # AI system prompt
├── src/
│   ├── models/            # Pydantic data models
│   ├── services/          # Business logic services
│   ├── ui/                # User interface components
│   └── utils/             # Shared utilities
├── public/                # Static assets
├── branding/              # Brand assets and logos
├── main.py                # Application entry point
└── requirements.txt       # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions:
- Open an issue on GitHub
- Contact the development team

---

*"Your journey, together" – MammoChat™* 💗