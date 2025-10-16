#!/usr/bin/env python3
"""
Trademark Symbol Validation Tests for MammoChat™.

This module contains comprehensive tests to ensure the proper trademark symbol "MammoChat™"
is always used instead of "MammoChatTM" in key configuration files and user-facing content.

The tests validate:
- Key configuration files (app.json, scene.json, manifest.json)
- User-facing strings and content
- Consistency across the application
- Absence of incorrect "MammoChatTM" format
"""

import json
import os
from pathlib import Path


class TestTrademarkValidation:
    """Test class for validating proper trademark symbol usage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.public_dir = self.project_root / "public"

    def test_config_app_json_trademark(self):
        """Test that app.json contains proper trademark symbol."""
        app_json_path = self.config_dir / "app.json"

        with app_json_path.open(encoding="utf-8") as f:
            app_config = json.load(f)

        # Check main app name
        assert (
            "MammoChat™" in app_config["app"]["name"]
        ), f"app.json missing proper trademark symbol in app name: {app_config['app']['name']}"

        # Verify no incorrect format exists
        assert (
            "MammoChatTM" not in app_config["app"]["name"]
        ), f"app.json contains incorrect trademark format: {app_config['app']['name']}"

    def test_config_scene_json_trademark(self):
        """Test that scene.json contains proper trademark symbol."""
        scene_json_path = self.config_dir / "scene.json"

        with scene_json_path.open(encoding="utf-8") as f:
            scene_config = json.load(f)

        # Check logo alt text
        logo_alt = scene_config.get("logo", {}).get("alt", "")
        assert (
            logo_alt == "MammoChat™"
        ), f"scene.json logo alt text missing proper trademark symbol: {logo_alt}"

        # Verify no incorrect format exists
        assert (
            "MammoChatTM" not in logo_alt
        ), f"scene.json contains incorrect trademark format in logo alt: {logo_alt}"

    def test_manifest_json_trademark(self):
        """Test that manifest.json contains proper trademark symbols."""
        manifest_path = self.public_dir / "manifest.json"

        with manifest_path.open(encoding="utf-8") as f:
            manifest = json.load(f)

        # Check name field
        assert (
            manifest["name"] == "MammoChat™"
        ), f"manifest.json name missing proper trademark symbol: {manifest['name']}"

        # Check short_name field
        assert (
            manifest["short_name"] == "MammoChat™"
        ), f"manifest.json short_name missing proper trademark symbol: {manifest['short_name']}"

        # Verify no incorrect format exists in either field
        assert (
            "MammoChatTM" not in manifest["name"]
        ), f"manifest.json name contains incorrect trademark format: {manifest['name']}"
        assert (
            "MammoChatTM" not in manifest["short_name"]
        ), f"manifest.json short_name contains incorrect trademark format: {manifest['short_name']}"

    def test_user_facing_strings_trademark(self):
        """Test that user-facing strings contain proper trademark symbols."""
        # Test main.py title
        main_py_path = self.project_root / "main.py"
        with main_py_path.open(encoding="utf-8") as f:
            main_content = f.read()

        # Check UI title in main.py
        assert (
            'title="MammoChat™ - Your journey, together"' in main_content
        ), "main.py missing proper trademark symbol in UI title"

        # Verify no incorrect format exists
        assert (
            "MammoChatTM" not in main_content
        ), "main.py contains incorrect trademark format"

    def test_welcome_message_trademark(self):
        """Test that welcome message contains proper trademark symbol."""
        scene_json_path = self.config_dir / "scene.json"

        with scene_json_path.open(encoding="utf-8") as f:
            scene_config = json.load(f)

        welcome_message = scene_config.get("chat", {}).get("welcome_message", "")

        # Check welcome message contains proper trademark symbol
        assert (
            "MammoChat™" in welcome_message
        ), f"Welcome message missing proper trademark symbol: {welcome_message}"

        # Verify no incorrect format exists
        assert (
            "MammoChatTM" not in welcome_message
        ), f"Welcome message contains incorrect trademark format: {welcome_message}"

    def test_source_files_trademark_consistency(self):
        """Test that source files maintain trademark consistency."""
        source_files = [
            "src/services/chat_service.py",
            "src/services/memory_service.py",
            "src/ui/main_ui.py",
            "src/utils/__init__.py",
            "src/utils/exceptions.py",
        ]

        for file_path in source_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with full_path.open(encoding="utf-8") as f:
                    content = f.read()

                # Check for proper trademark symbol in docstrings and comments
                if "MammoChat" in content:
                    assert (
                        "MammoChat™" in content
                    ), f"{file_path} missing proper trademark symbol"

                    # Verify no incorrect format exists
                    assert (
                        "MammoChatTM" not in content
                    ), f"{file_path} contains incorrect trademark format"

    def test_documentation_files_trademark(self):
        """Test that documentation files contain proper trademark symbols."""
        doc_files = ["README.md", "CONTRIBUTING.md", "TESTING.md", "docs/API.md"]

        for file_path in doc_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with full_path.open(encoding="utf-8") as f:
                    content = f.read()

                # Check for proper trademark symbol
                if "MammoChat" in content:
                    assert (
                        "MammoChat™" in content
                    ), f"{file_path} missing proper trademark symbol"

                    # Verify no incorrect format exists
                    assert (
                        "MammoChatTM" not in content
                    ), f"{file_path} contains incorrect trademark format"

    def test_branding_files_trademark(self):
        """Test that branding files contain proper trademark symbols."""
        branding_files = [
            "branding/BRAND_GUIDELINES.md",
            "branding/IMPLEMENTATION_GUIDE.md",
            "branding/PACKAGE_SUMMARY.md",
            "branding/COMPLETE_SUMMARY.md",
        ]

        for file_path in branding_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with full_path.open(encoding="utf-8") as f:
                    content = f.read()

                # Check for proper trademark symbol
                if "MammoChat" in content:
                    assert (
                        "MammoChat™" in content
                    ), f"{file_path} missing proper trademark symbol"

                    # Verify no incorrect format exists
                    assert (
                        "MammoChatTM" not in content
                    ), f"{file_path} contains incorrect trademark format"

    def test_no_incorrect_trademark_format_anywhere(self):
        """Test that no files contain the incorrect 'MammoChatTM' format."""
        # Search for any instances of incorrect format in the entire codebase
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories that might contain generated content
            skip_dirs = {
                ".git",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
            }
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                if file.endswith(
                    (".py", ".json", ".md", ".txt", ".html", ".js", ".ts")
                ):
                    file_path = Path(root) / file

                    # Skip the test file itself since it contains the string for testing
                    if file_path.name == "test_trademark_validation.py":
                        continue

                    try:
                        with file_path.open(encoding="utf-8") as f:
                            content = f.read()

                        # Check for incorrect format
                        assert (
                            "MammoChatTM" not in content
                        ), f"File {file_path} contains incorrect trademark format 'MammoChatTM'"

                    except (UnicodeDecodeError, PermissionError):
                        # Skip files that can't be read as text
                        continue

    def test_critical_files_have_trademark(self):
        """Test that all critical files contain at least one instance of proper trademark symbol."""
        critical_files = [
            "config/app.json",
            "config/scene.json",
            "public/manifest.json",
            "main.py",
            "README.md",
        ]

        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                with full_path.open(encoding="utf-8") as f:
                    content = f.read()

                assert (
                    "MammoChat™" in content
                ), f"Critical file {file_path} missing proper trademark symbol"


if __name__ == "__main__":
    # Run the tests
    test_instance = TestTrademarkValidation()
    test_instance.setup_method()

    print("🧪 Running MammoChat™ Trademark Validation Tests...")

    try:
        test_instance.test_config_app_json_trademark()
        print("✅ app.json trademark validation passed")

        test_instance.test_config_scene_json_trademark()
        print("✅ scene.json trademark validation passed")

        test_instance.test_manifest_json_trademark()
        print("✅ manifest.json trademark validation passed")

        test_instance.test_user_facing_strings_trademark()
        print("✅ User-facing strings trademark validation passed")

        test_instance.test_welcome_message_trademark()
        print("✅ Welcome message trademark validation passed")

        test_instance.test_source_files_trademark_consistency()
        print("✅ Source files trademark consistency validation passed")

        test_instance.test_documentation_files_trademark()
        print("✅ Documentation files trademark validation passed")

        test_instance.test_branding_files_trademark()
        print("✅ Branding files trademark validation passed")

        test_instance.test_no_incorrect_trademark_format_anywhere()
        print("✅ No incorrect trademark format found anywhere")

        test_instance.test_critical_files_have_trademark()
        print("✅ All critical files have proper trademark symbols")

        print(
            "\n🎉 All trademark validation tests passed! MammoChat™ branding is consistent."
        )

    except AssertionError as e:
        print(f"\n❌ Trademark validation failed: {e}")
        raise
    except Exception as e:
        print(f"\n💥 Unexpected error during trademark validation: {e}")
        raise
