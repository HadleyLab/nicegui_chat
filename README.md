# MammoChat 💗

*Your journey, together*

A compassionate AI-powered web application designed to support breast cancer patients through clinical trial discovery, treatment navigation, and peer community connections. Built with NiceGUI, HeySol memory management, and DeepSeek AI.

## ✨ Features

- 💗 **Compassionate Support** – Warm, empathetic guidance throughout your healthcare journey
- � **Clinical Trial Matching** – Find trials that match your diagnosis and preferences
- 🧠 **Memory-Enhanced Conversations** – Never repeat yourself; we remember your story
- 💬 **Real-time AI Assistance** – Streaming responses with natural conversation flow
- � **Community Connections** – Access to supportive peer groups who understand
- 🎨 **Feminine, Modern Design** – Soft pinks and grays in a trustworthy, professional interface
- 📱 **Responsive & Accessible** – Works beautifully on all devices, WCAG AA compliant
- 🔐 **Secure & Private** – Your healthcare information stays confidential

## 🎯 Purpose

MammoChat empowers breast cancer patients by:
- Connecting them with relevant clinical trials
- Providing clear, compassionate information about treatment options
- Facilitating peer support and community connections
- Remembering their journey so they feel heard and understood
- Supporting informed decision-making with medical credibility

## 🚀 Quick Start

### Option 1: Local Development

#### Prerequisites
- Python 3.9 or higher
- API keys for DeepSeek and HeySol (required for full functionality)

#### Installation
1. **Clone or download the repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your actual API keys:
# - DEEPSEEK_API_KEY (required)
# - HEYSOL_API_KEY (optional, for memory features)
```

4. **Run the application:**
```bash
python main.py
# or
python run.py
# or
bash run.sh
```

5. **Open your browser:**
    Navigate to `http://localhost:8080`

### Option 2: Docker Deployment (Recommended)

#### Quick Docker Deployment
```bash
# 1. Set up API keys
cp .env.example .env
# Edit .env with your API keys

# 2. Build and run with Docker Compose
docker compose up --build -d

# 3. Access the application
# Open http://localhost:8080
```

#### Production Deployment
```bash
# Build for production
docker build -t mammochat:latest .

# Run with Docker Compose
docker compose up -d

# Or run directly
docker run -d \
  --name mammochat \
  -p 8080:8080 \
  -e DEEPSEEK_API_KEY=your_key \
  -e HEYSOL_API_KEY=your_heysol_key \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/branding:/app/branding:ro \
  -v $(pwd)/prompts:/app/prompts:ro \
  mammochat:latest
```

#### Remote Deployment (NAS/Servers)
```bash
# Copy files to remote server
scp -r . user@remote-server:/path/to/mammochat

# Run on remote server
ssh user@remote-server "cd /path/to/mammochat && docker compose up --build -d"
```

See [DOCKER_README.md](DOCKER_README.md) for complete Docker deployment guide.

## 🎨 Design Features

### MammoChat Brand Identity
- **Feminine & Modern** aesthetic with medical credibility
- **Soft color palette** using pinks, grays, and light tones
- **Heart icon** symbolizing care and compassion
- **Community-focused** design language
- **Trustworthy typography** using Inter font family

### Color Scheme
- Primary: Rose Quartz (#F4B8C5)
- Accent: Soft Mauve (#E8A0B8)
- Background: Cloud Gray (#FAFBFC)
- Surface: White (#FFFFFF)
- Text: Charcoal (#334155)

### UI Elements
- **Rounded corners** for soft, approachable feel
- **Gradient buttons** with pink accents
- **Smooth animations** with 300ms transitions
- **Welcome message** explaining MammoChat's purpose
- **Heart icon** in header with tagline "Your journey, together"
- **Compassionate copy** throughout the interface

### Animations
- Message slide-in: 0.3s ease-out
- Typing indicator: Pulsing dots in soft mauve
- Button hover: Subtle scale with pink glow
- Input focus: Pink border with soft shadow

## 🏗️ Architecture

The application follows a clean, layered architecture inspired by the beeware_chat project:

```
┌─────────────────────────────────────┐
│          UI Layer (NiceGUI)         │
│  - MammoChat branded interface      │
│  - Message rendering                │
│  - Input handling                   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         Services Layer              │
│  - ChatService (orchestration)      │
│  - AuthService (HeySol client)      │
│  - MemoryService (memory ops)       │
│  - AgentService (Pydantic AI)       │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         Models Layer                │
│  - Pydantic models for validation   │
│  - Chat models (messages, state)    │
│  - Memory models (episodes, spaces) │
└─────────────────────────────────────┘
```

### Key Components

#### Services
- **AuthService**: Manages HeySol authentication and client lifecycle
- **MemoryService**: Handles HeySol memory operations (search, add, list spaces)
- **ChatAgent**: Wraps Pydantic AI agent with DeepSeek LLM
- **ChatService**: Orchestrates chat flow with streaming responses

#### Models
- **Pydantic models** for type safety and validation
- **Chat models**: ConversationState, ChatMessage, MessageRole, etc.
- **Memory models**: MemoryEpisode, MemorySearchResult, MemorySpace

#### UI
- **NiceGUI-based** modern web interface
- **Responsive design** with Tailwind CSS classes
- **Smooth animations** and transitions
- **Real-time streaming** chat responses

## 📋 Configuration

### Secrets (.env)

**Only API keys are stored in the `.env` file** (never commit this file):

```bash
# API Keys (Secrets only - keep this file secure!)

# DeepSeek API Key (Required for AI chat responses)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# HeySol API Key (Optional - enables memory features)
HEYSOL_API_KEY=your_heysol_api_key_here
```

### Application Configuration (config/app_config.json)

**All non-secret configuration** is in JSON for easy customization:

```json
{
  "app": {
    "name": "MammoChat",
    "host": "0.0.0.0",
    "port": 8080,
    "reload": false
  },
  },
  "llm": {
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com"
  },
  "heysol": {
    "base_url": "https://core.heysol.ai/api/v1"
  },
  "chat": {
    "enable_memory_enrichment": true,
    "store_user_messages": true,
    "stream_chunk_size": 50,
    "max_history_display": 50
  },
  "ui": {
    "theme": "light",
    "primary_color": "#F4B8C5",
    "tagline": "Your journey, together",
    "logo_full_path": "/branding/logo-full-color.svg",
    "logo_icon_path": "/branding/logo-icon.svg",
    "welcome_title": "Welcome to MammoChat",
    "welcome_message": "...",
    "input_placeholder": "Type your message...",
    "thinking_text": "Thinking...",
    "send_tooltip": "Send Message",
    "dark_mode_tooltip": "Toggle Dark Mode",
    "new_conversation_tooltip": "New Conversation",
    "logout_tooltip": "Logout"
  }
}
```

**Benefits of Configuration-Driven UI:**
- 🌍 Easy to internationalize/localize
- 🎨 Simple rebranding without code changes
- 📊 A/B testing different messaging
- 🔧 No code deployment for text updates

## 🛠️ Development

### Project Structure
See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development documentation.

### Testing
```bash
# Run comprehensive test suite
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run basic integration test
python test_setup.py
```

**Comprehensive Testing Suite:**
- **143 passing tests** with 95% code coverage
- **Unit tests** for all core modules (config, models, services)
- **Integration tests** for chat service workflows
- **Async testing** support for all async operations
- **Mocking infrastructure** for external API dependencies
- **CI/CD ready** with automated coverage reporting

**Test Coverage Breakdown:**
- ✅ **100% coverage**: Exceptions, Chat models, Memory models, Chat service
- ✅ **95% coverage**: Configuration management
- ✅ **87-90% coverage**: Auth service, Memory service, Agent service
- ✅ **UI components excluded** (complex to test, not core functionality)

**Testing Standards:**
- **Fail Fast**: Tests fail immediately on any deviation
- **Explicit Coverage**: Every code path tested with clear assertions
- **Speed First**: Minimal test overhead and fast execution
- **Type Safety**: Full mypy compliance
- **Code Quality**: ruff/black/isort validation

## 🔒 Security

- API keys stored securely in `.env` file
- `.env` file excluded from git via `.gitignore`
- No hardcoded credentials in source code
- Environment variable support for all sensitive data

## 🎯 Usage

1. **Start a conversation**: Type your message and press Enter or click Send
2. **Get AI responses**: The assistant streams responses in real-time
3. **Memory integration**: The AI automatically searches memory for context
4. **New conversation**: Click the refresh button to start fresh
5. **Logout**: Click the logout button to end your session

## 📚 Dependencies

- **nicegui**: Modern Python UI framework
- **pydantic**: Data validation and settings management
- **pydantic-ai**: AI agent framework
- **heysol-api-client**: HeySol memory API client
- **python-dotenv**: Environment variable management
- **structlog**: Structured logging

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project follows the patterns established in beeware_chat and is provided as-is for educational and development purposes.

## 🙏 Acknowledgments

- Architecture inspired by the beeware_chat project
- UI framework powered by NiceGUI
- AI capabilities from DeepSeek
- Memory features from HeySol API

