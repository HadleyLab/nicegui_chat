"""
Quick demonstration of the NiceGUI Chat application.

This script shows the key features and components of the application.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_header():
    """Print application header."""
    print("\n" + "=" * 70)
    print("🤖 NiceGUI Chat - Modern AI Chat Application")
    print("=" * 70)
    print()


def print_features():
    """Print application features."""
    print("✨ Features:")
    print("  • Modern, minimalistic UI with smooth animations")
    print("  • Real-time streaming chat responses")
    print("  • Memory-enhanced conversations via HeySol API")
    print("  • Context-aware AI powered by DeepSeek")
    print("  • Responsive design for desktop and mobile")
    print("  • Secure API key management")
    print()


def print_architecture():
    """Print architecture overview."""
    print("🏗️  Architecture:")
    print("  • UI Layer: NiceGUI-based modern web interface")
    print("  • Services: Auth, Memory, Chat, and AI Agent services")
    print("  • Models: Pydantic models for type safety")
    print("  • Config: JSON + environment variable configuration")
    print()


def print_tech_stack():
    """Print technology stack."""
    print("🔧 Technology Stack:")
    print("  • NiceGUI - Python web UI framework")
    print("  • Pydantic AI - AI agent framework")
    print("  • DeepSeek - Large language model")
    print("  • HeySol API - Memory management")
    print("  • Python 3.9+ - Programming language")
    print()


def print_usage():
    """Print usage instructions."""
    print("🚀 Quick Start:")
    print("  1. Configure your API keys in .env file")
    print("  2. Run: python main.py")
    print("  3. Open: http://localhost:8080")
    print("  4. Start chatting with the AI assistant!")
    print()
    print("📝 Alternative ways to start:")
    print("  • python run.py")
    print("  • bash run.sh")
    print()


def check_config():
    """Check configuration status."""
    print("⚙️  Configuration Status:")
    try:
        from src.config import load_app_config
        config = load_app_config()
        
        # Check DeepSeek
        if config.llm.api_key:
            print("  ✓ DeepSeek API key configured")
        else:
            print("  ✗ DeepSeek API key NOT configured (required)")
        
        # Check HeySol
        if config.heysol.api_key:
            print("  ✓ HeySol API key configured (memory enabled)")
        else:
            print("  ⚠ HeySol API key NOT configured (memory disabled)")
        
        print(f"  • App will run on {config.app.host}:{config.app.port}")
        print()
        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        print()
        return False


def print_customization():
    """Print customization options."""
    print("🎨 Customization:")
    print("  • UI Theme: Edit config/app_config.json → ui section")
    print("  • System Prompt: Edit prompts/system.md")
    print("  • Chat Behavior: Edit config/app_config.json → chat section")
    print("  • Colors & Animations: Modify ui config values")
    print()


def print_footer():
    """Print footer with helpful links."""
    print("=" * 70)
    print("📚 Documentation:")
    print("  • README.md - Full documentation")
    print("  • DEVELOPMENT.md - Development guide")
    print("  • test_setup.py - System verification")
    print()
    print("💡 Tips:")
    print("  • Use Ctrl+C to stop the server")
    print("  • Check test_setup.py output for system verification")
    print("  • Memory features require HeySol API key")
    print("=" * 70)
    print()


def main():
    """Run the demonstration."""
    print_header()
    print_features()
    print_architecture()
    print_tech_stack()
    
    config_ok = check_config()
    
    print_usage()
    print_customization()
    print_footer()
    
    if not config_ok:
        print("⚠️  Please fix configuration issues before running the application.")
        print()
        return 1
    
    # Ask if user wants to start the application
    try:
        response = input("Would you like to start the application now? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            print("\n🚀 Starting NiceGUI Chat...")
            print("📍 Open your browser at: http://localhost:8080")
            print("Press Ctrl+C to stop the server\n")
            from main import main as run_app
            run_app()
        else:
            print("\n👋 You can start the application anytime with: python main.py")
            print()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
