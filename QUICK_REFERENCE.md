# Quick Reference Guide

## Start the Application

```bash
python main.py
```

## File Structure Quick Reference

| File/Directory | Purpose |
|---------------|---------|
| `main.py` | Application entry point |
| `config/app_config.json` | App configuration |
| `prompts/system.md` | AI system prompt |
| `src/config.py` | Config loader |
| `src/models/` | Data models |
| `src/services/` | Business logic |
| `src/ui/` | User interface |
| `.env` | API keys (secrets) |

## Configuration Quick Reference

### .env File
```bash
DEEPSEEK_API_KEY=your_key_here      # Required
HEYSOL_API_KEY=your_key_here        # Optional (for memory)
APP_HOST=0.0.0.0
APP_PORT=8080
```

### app_config.json - UI Theme
```json
{
  "ui": {
    "primary_color": "#6366f1",
    "background_color": "#0f172a",
    "surface_color": "#1e293b",
    "text_color": "#e2e8f0"
  }
}
```

### app_config.json - Chat Behavior
```json
{
  "chat": {
    "enable_memory_enrichment": true,
    "store_user_messages": true,
    "stream_chunk_size": 50
  }
}
```

## Common Tasks

### Change UI Colors
Edit `config/app_config.json` → `ui` section

### Customize AI Behavior
Edit `prompts/system.md`

### Change Streaming Speed
Edit `config/app_config.json` → `chat.stream_chunk_size`

### Disable Memory Features
Set `HEYSOL_API_KEY=""` in `.env`

## Testing

```bash
python test_setup.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | Run `pip install -r requirements.txt` |
| "Config not found" | Ensure `config/app_config.json` exists |
| "API key error" | Check `.env` file has correct keys |
| Port already in use | Change `APP_PORT` in `.env` |

## Architecture Flow

```
User Input → ChatUI → ChatService → ChatAgent → DeepSeek LLM
                ↓                      ↓
          ConversationState    MemoryService → HeySol API
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `ChatUI` | NiceGUI interface |
| `ChatService` | Orchestrates chat flow |
| `ChatAgent` | Pydantic AI agent |
| `AuthService` | HeySol authentication |
| `MemoryService` | Memory operations |
| `ConversationState` | Chat state management |

## Important URLs

- Local: `http://localhost:8080`
- DeepSeek API: `https://api.deepseek.com`
- HeySol API: `https://core.heysol.ai/api/v1`

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | Yes | - | DeepSeek API key |
| `HEYSOL_API_KEY` | No | - | HeySol API key |
| `APP_NAME` | No | "NiceGUI Chat" | App name |
| `APP_HOST` | No | "0.0.0.0" | Host address |
| `APP_PORT` | No | 8080 | Port number |
| `APP_RELOAD` | No | False | Auto-reload |

## Dependencies

```
nicegui>=1.4.0
pydantic>=2.7.0
pydantic-ai>=0.8.0
python-dotenv>=1.0.0
heysol-api-client>=1.2.1
structlog>=24.1.0
aiofiles>=23.0.0
```

## Useful Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_setup.py

# Run demo
python demo.py

# Start app
python main.py

# Start with auto-reload
# Set APP_RELOAD=True in .env
python main.py
```

## Customization Examples

### Change Primary Color to Blue
```json
{
  "ui": {
    "primary_color": "#3b82f6"
  }
}
```

### Increase Streaming Speed
```json
{
  "chat": {
    "stream_chunk_size": 100
  }
}
```

### Change System Prompt
Edit `prompts/system.md` with your custom prompt.

## Performance Tips

1. Lower `stream_chunk_size` for faster perceived responses
2. Disable `enable_memory_enrichment` if not using memory
3. Set `store_user_messages: false` to reduce memory usage
4. Use `APP_RELOAD=False` in production

## Security Checklist

- [ ] `.env` file not committed to git
- [ ] Strong API keys configured
- [ ] `APP_HOST` set appropriately for deployment
- [ ] Firewall rules configured for production
- [ ] HTTPS enabled in production

## Support

- Documentation: `README.md`
- Development Guide: `DEVELOPMENT.md`
- Project Summary: `PROJECT_SUMMARY.md`
- Issues: Check test output from `test_setup.py`
