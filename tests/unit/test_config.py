"""Unit tests for configuration management."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import (
    AppMetadata,
    ChatConfig,
    DeepSeekConfig,
    HeysolConfig,
    PromptStore,
    UIConfig,
    load_app_config,
)
from src.utils.exceptions import ConfigurationError


class TestPromptStore:
    """Test PromptStore lazy loading functionality."""

    def test_prompt_store_creation(self):
        """Test PromptStore creation."""
        root = Path("/tmp/prompts")
        store = PromptStore(root)

        assert store.root == root
        assert store._cache == {}

    def test_prompt_store_read_existing_file(self, tmp_path):
        """Test reading an existing prompt file."""
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "test.md"
        content = "Test prompt content"
        prompt_file.write_text(content)

        store = PromptStore(prompt_dir)
        result = store.read("test")

        assert result == content

    def test_prompt_store_read_caches_result(self, tmp_path):
        """Test that read caches results."""
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "cached.md"
        content = "Cached content"
        prompt_file.write_text(content)

        store = PromptStore(prompt_dir)

        # First read
        result1 = store.read("cached")
        assert result1 == content
        assert "cached" in store._cache

        # Second read should use cache
        result2 = store.read("cached")
        assert result2 == content
        assert store._cache["cached"] == content

    def test_prompt_store_read_missing_file(self, tmp_path):
        """Test reading a missing prompt file raises error."""
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()

        store = PromptStore(prompt_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            store.read("missing")

        assert "missing" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_prompt_store_optional_existing_file(self, tmp_path):
        """Test optional read with existing file."""
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "optional.md"
        content = "Optional content"
        prompt_file.write_text(content)

        store = PromptStore(prompt_dir)
        result = store.optional("optional")

        assert result == content

    def test_prompt_store_optional_missing_file(self, tmp_path):
        """Test optional read with missing file returns default."""
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()

        store = PromptStore(prompt_dir)
        result = store.optional("missing", "default value")

        assert result == "default value"

    def test_prompt_store_optional_missing_file_no_default(self, tmp_path):
        """Test optional read with missing file and no default returns empty string."""
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()

        store = PromptStore(prompt_dir)
        result = store.optional("missing")

        assert result == ""


class TestChatConfig:
    """Test ChatConfig dataclass."""

    def test_chat_config_creation_valid(self):
        """Test ChatConfig creation with valid data."""
        config = ChatConfig(
            enable_memory_enrichment=True,
            store_user_messages=True,
            stream_chunk_size=50,
            max_history_display=100,
        )

        assert config.enable_memory_enrichment is True
        assert config.store_user_messages is True
        assert config.stream_chunk_size == 50
        assert config.max_history_display == 100

    def test_chat_config_from_payload_valid(self):
        """Test ChatConfig.from_payload with valid data."""
        payload = {
            "enable_memory_enrichment": False,
            "store_user_messages": False,
            "stream_chunk_size": 25,
            "max_history_display": 50,
        }

        config = ChatConfig.from_payload(payload)

        assert config.enable_memory_enrichment is False
        assert config.store_user_messages is False
        assert config.stream_chunk_size == 25
        assert config.max_history_display == 50

    def test_chat_config_from_payload_defaults(self):
        """Test ChatConfig.from_payload with missing values uses defaults."""
        payload = {}

        config = ChatConfig.from_payload(payload)

        assert config.enable_memory_enrichment is True  # default
        assert config.store_user_messages is True  # default
        assert config.stream_chunk_size == 50  # default
        assert config.max_history_display == 50  # default

    def test_chat_config_from_payload_invalid_types(self):
        """Test ChatConfig.from_payload with invalid types."""
        payload = {
            "enable_memory_enrichment": "not_a_bool",
            "store_user_messages": "not_a_bool",
            "stream_chunk_size": "not_an_int",
            "max_history_display": "not_an_int",
        }

        with pytest.raises(ConfigurationError):
            ChatConfig.from_payload(payload)


class TestDeepSeekConfig:
    """Test DeepSeekConfig dataclass."""

    def test_deepseek_config_creation_valid(self):
        """Test DeepSeekConfig creation with valid data."""
        config = DeepSeekConfig(
            api_key="test-key",
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            system_prompt="Test prompt",
        )

        assert config.api_key == "test-key"
        assert config.model == "deepseek-chat"
        assert config.base_url == "https://api.deepseek.com"
        assert config.system_prompt == "Test prompt"

    def test_deepseek_config_ensure_valid_success(self):
        """Test ensure_valid with valid config."""
        config = DeepSeekConfig(
            api_key="valid-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt",
        )

        # Should not raise
        config.ensure_valid()

    def test_deepseek_config_ensure_valid_missing_api_key(self):
        """Test ensure_valid with missing API key."""
        config = DeepSeekConfig(
            api_key="",
            model="test-model",
            base_url="https://test.com",
            system_prompt="Test prompt",
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.ensure_valid()

        assert "DEEPSEEK_API_KEY" in str(exc_info.value)

    def test_deepseek_config_ensure_valid_missing_prompt(self):
        """Test ensure_valid with missing system prompt."""
        config = DeepSeekConfig(
            api_key="valid-key",
            model="test-model",
            base_url="https://test.com",
            system_prompt="",
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.ensure_valid()

        assert "System prompt" in str(exc_info.value)


class TestHeysolConfig:
    """Test HeysolConfig dataclass."""

    def test_heysol_config_creation_with_api_key(self):
        """Test HeysolConfig creation with API key."""
        config = HeysolConfig(
            api_key="test-key", base_url="https://core.heysol.ai/api/v1"
        )

        assert config.api_key == "test-key"
        assert config.base_url == "https://core.heysol.ai/api/v1"

    def test_heysol_config_creation_without_api_key(self):
        """Test HeysolConfig creation without API key."""
        config = HeysolConfig(api_key=None, base_url="https://core.heysol.ai/api/v1")

        assert config.api_key is None
        assert config.base_url == "https://core.heysol.ai/api/v1"


class TestUIConfig:
    """Test UIConfig dataclass."""

    def test_ui_config_from_payload_valid(self):
        """Test UIConfig.from_payload with valid data."""
        payload = {
            "theme": "dark",
            "primary_color": "#ff0000",
            "background_color": "#000000",
            "surface_color": "#111111",
            "text_color": "#ffffff",
            "accent_color": "#00ff00",
            "border_radius": "8px",
            "animation_duration": "0.2s",
            "tagline": "Test tagline",
            "logo_full_path": "/branding/logo-full.svg",
            "logo_icon_path": "/branding/logo-icon.svg",
            "welcome_title": "Test Welcome",
            "welcome_message": "Test message",
            "input_placeholder": "Test placeholder",
            "thinking_text": "Test thinking",
            "send_tooltip": "Test send",
            "dark_mode_tooltip": "Test dark mode",
            "new_conversation_tooltip": "Test new conv",
            "logout_tooltip": "Test logout",
            "new_conversation_notification": "Test new conv notif",
            "logout_notification": "Test logout notif",
            "response_complete_notification": "Test response notif",
        }

        config = UIConfig.from_payload(payload)

        assert config.theme == "dark"
        assert config.primary_color == "#ff0000"
        assert config.welcome_title == "Test Welcome"
        assert config.send_tooltip == "Test send"

    def test_ui_config_from_payload_defaults(self):
        """Test UIConfig.from_payload with empty payload uses defaults."""
        payload = {}

        config = UIConfig.from_payload(payload)

        assert config.theme == "dark"
        assert config.primary_color == "#6366f1"
        assert config.welcome_title == "Welcome to MammoChat"
        assert config.input_placeholder == "Type your message..."
        assert config.thinking_text == "Thinking..."


class TestAppMetadata:
    """Test AppMetadata dataclass."""

    def test_app_metadata_from_payload_valid(self):
        """Test AppMetadata.from_payload with valid data."""
        payload = {
            "name": "Test App",
            "host": "127.0.0.1",
            "port": 3000,
            "reload": True,
        }

        config = AppMetadata.from_payload(payload)

        assert config.name == "Test App"
        assert config.host == "127.0.0.1"
        assert config.port == 3000
        assert config.reload is True

    def test_app_metadata_from_payload_defaults(self):
        """Test AppMetadata.from_payload with empty payload uses defaults."""
        payload = {}

        config = AppMetadata.from_payload(payload)

        assert config.name == "NiceGUI Chat"
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.reload is False

    def test_app_metadata_from_payload_invalid_port(self):
        """Test AppMetadata.from_payload with invalid port type."""
        payload = {"port": "not_a_number"}

        with pytest.raises(ValueError):
            AppMetadata.from_payload(payload)


class TestLoadAppConfig:
    """Test load_app_config function."""

    def test_load_app_config_success(self, tmp_path, mock_env_vars):
        """Test successful config loading."""
        # Create config file
        config_file = tmp_path / "test_config.json"
        config_data = {
            "app": {"name": "Test App", "port": 3000},
            "chat": {"stream_chunk_size": 25},
            "llm": {"model": "test-model", "base_url": "https://test.com"},
            "heysol": {"base_url": "https://heysol.test"},
            "prompts": {"root": str(tmp_path / "prompts"), "system": "system"},
            "ui": {"theme": "light"},
        }
        config_file.write_text(json.dumps(config_data))

        # Create prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "system.md"
        test_prompt_content = "System prompt content"
        prompt_file.write_text(test_prompt_content)

        with patch.dict(os.environ, {"APP_CONFIG_PATH": str(config_file)}):
            config = load_app_config()

        assert config.app.name == "Test App"
        assert config.app.port == 3000
        assert config.chat.stream_chunk_size == 25
        assert config.llm.api_key == "test_deepseek_key"
        assert config.heysol.api_key == "test_heysol_key"
        assert config.llm.system_prompt == test_prompt_content

    def test_load_app_config_missing_config_file(self):
        """Test load_app_config with missing config file."""
        with patch.dict(os.environ, {"APP_CONFIG_PATH": "/nonexistent/config.json"}):
            with pytest.raises(ConfigurationError) as exc_info:
                load_app_config()

            assert "not found" in str(exc_info.value)

    def test_load_app_config_invalid_json(self, tmp_path):
        """Test load_app_config with invalid JSON."""
        config_file = tmp_path / "invalid_config.json"
        config_file.write_text("invalid json content")

        with patch.dict(os.environ, {"APP_CONFIG_PATH": str(config_file)}):
            with pytest.raises(ConfigurationError) as exc_info:
                load_app_config()

            assert "Failed to read config" in str(exc_info.value)

    def test_load_app_config_missing_required_sections(self, tmp_path):
        """Test load_app_config with missing required sections."""
        config_file = tmp_path / "incomplete_config.json"
        config_data = {
            "app": {"name": "Test"},
            # Missing chat, llm, heysol, prompts sections
        }
        config_file.write_text(json.dumps(config_data))

        with patch.dict(os.environ, {"APP_CONFIG_PATH": str(config_file)}):
            with pytest.raises(ConfigurationError):
                load_app_config()

    def test_load_app_config_missing_prompt_file(self, tmp_path):
        """Test load_app_config with missing prompt file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "app": {"name": "Test"},
            "chat": {},
            "llm": {"model": "test", "base_url": "https://test.com"},
            "heysol": {"base_url": "https://heysol.test"},
            "prompts": {"root": "prompts", "system": "missing"},
            "ui": {},
        }
        config_file.write_text(json.dumps(config_data))

        # Create prompt directory but not the file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()

        with patch.dict(os.environ, {"APP_CONFIG_PATH": str(config_file)}):
            with pytest.raises(ConfigurationError) as exc_info:
                load_app_config()

            assert "not found" in str(exc_info.value)

    def test_load_app_config_default_path(self, tmp_path, mock_env_vars):
        """Test load_app_config using default path."""
        # Create config in default location relative to tmp_path
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "app_config.json"
        config_data = {
            "app": {"name": "Default Config"},
            "chat": {},
            "llm": {"model": "test", "base_url": "https://test.com"},
            "heysol": {"base_url": "https://heysol.test"},
            "prompts": {"root": str(tmp_path / "prompts"), "system": "system"},
            "ui": {},
        }
        config_file.write_text(json.dumps(config_data))

        # Create prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "system.md"
        test_prompt = "Default system prompt"
        prompt_file.write_text(test_prompt)

        # Mock the default config path to point to our test config
        with patch("src.config.DEFAULT_CONFIG_PATH", config_file):
            with patch.dict(os.environ, {}, clear=True):  # No APP_CONFIG_PATH
                config = load_app_config()

        assert config.app.name == "Default Config"
        assert config.llm.system_prompt == test_prompt

    def test_load_app_config_environment_variable_override(
        self, tmp_path, mock_env_vars
    ):
        """Test that environment variables override config file values."""
        config_file = tmp_path / "config.json"
        config_data = {
            "app": {"name": "Config File Name"},
            "chat": {},
            "llm": {"model": "config-file-model", "base_url": "https://config.com"},
            "heysol": {"base_url": "https://heysol.config"},
            "prompts": {"root": "prompts", "system": "system"},
            "ui": {},
        }
        config_file.write_text(json.dumps(config_data))

        # Create prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        prompt_file = prompt_dir / "system.md"
        prompt_file.write_text("System prompt")

        with patch.dict(
            os.environ,
            {
                "APP_CONFIG_PATH": str(config_file),
                "DEEPSEEK_API_KEY": "env-api-key",
                "HEYSOL_API_KEY": "env-heysol-key",
            },
        ):
            config = load_app_config()

        # Environment variables should override
        assert config.llm.api_key == "env-api-key"
        assert config.heysol.api_key == "env-heysol-key"

        # Config file values should be used for non-secret fields
        assert config.app.name == "Config File Name"
        assert config.llm.model == "config-file-model"
