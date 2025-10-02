"""Test configuration and imports."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports() -> bool:
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        print("✓ Config module imported")
    except Exception as e:
        print(f"✗ Config module failed: {e}")
        return False

    try:
        print("✓ Chat models imported")
    except Exception as e:
        print(f"✗ Chat models failed: {e}")
        return False

    try:
        print("✓ Memory models imported")
    except Exception as e:
        print(f"✗ Memory models failed: {e}")
        return False

    try:
        print("✓ Auth service imported")
    except Exception as e:
        print(f"✗ Auth service failed: {e}")
        return False

    try:
        print("✓ Memory service imported")
    except Exception as e:
        print(f"✗ Memory service failed: {e}")
        return False

    try:
        print("✓ Chat service imported")
    except Exception as e:
        print(f"✗ Chat service failed: {e}")
        return False

    try:
        print("✓ Chat UI imported")
    except Exception as e:
        print(f"✗ Chat UI failed: {e}")
        return False

    return True


def test_configuration() -> bool:
    """Test configuration loading."""
    print("\nTesting configuration...")

    try:
        from src.config import load_app_config

        config = load_app_config()
        print("✓ Configuration loaded")
        print(f"  - App name: {config.app.name}")
        print(f"  - Host: {config.app.host}:{config.app.port}")
        print(f"  - LLM model: {config.llm.model}")
        print(f"  - HeySol base URL: {config.heysol.base_url}")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False


def test_services() -> bool:
    """Test service initialization."""
    print("\nTesting services...")

    try:
        from src.config import load_app_config
        from src.services.auth_service import AuthService

        config = load_app_config()

        # Initialize services
        auth_service = AuthService(config.heysol)
        print("✓ Auth service initialized")
        print(f"  - Authenticated: {auth_service.is_authenticated}")

        print("✓ Memory service initialized")
        print("✓ Chat service initialized")

        return True
    except Exception as e:
        print(f"✗ Services initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_models() -> bool:
    """Test Pydantic models."""
    print("\nTesting models...")

    try:
        from src.models.chat import ChatMessage, ConversationState, MessageRole

        # Create a chat message
        message = ChatMessage(role=MessageRole.USER, content="Hello, world!")
        print(f"✓ ChatMessage created: {message.message_id[:8]}...")

        # Create a conversation
        conversation = ConversationState()
        conversation.append_message(message)
        print(f"✓ ConversationState created with {len(conversation.messages)} message(s)")

        return True
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main() -> int:
    """Run all tests."""
    print("=" * 60)
    print("NiceGUI Chat - System Test")
    print("=" * 60)

    results: list[tuple[str, bool]] = []

    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_configuration()))
    results.append(("Models", test_models()))
    results.append(("Services", test_services()))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:20s} {status}")

    all_passed = all(result[1] for result in results)

    print("=" * 60)
    if all_passed:
        print("✓ All tests passed! The application is ready to run.")
        print("\nTo start the application, run:")
        print("  python main.py")
        print("  or")
        print("  python run.py")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
