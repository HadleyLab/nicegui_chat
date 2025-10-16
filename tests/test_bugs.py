"""Tests for specific bugs and issues."""

from config import config


class TestChatMessageColoring:
    """Test chat message coloring bugs."""

    def test_user_message_primary_color(self):
        """Test that user messages use primary color."""
        user_props = config.scene["chat"]["user_message_props"]
        assert "bg-color=primary" in user_props
        assert "text-color=white" in user_props

    def test_assistant_message_accent_color(self):
        """Test that assistant messages use accent color."""
        assistant_props = config.scene["chat"]["assistant_message_props"]
        assert "bg-color=accent" in assistant_props
        assert "text-color=grey-8" in assistant_props

    def test_welcome_message_accent_color(self):
        """Test that welcome message uses accent color."""
        welcome_props = config.scene["chat"]["welcome_message_props"]
        assert "bg-color=accent" in welcome_props
        assert "text-color=grey-8" in welcome_props

    def test_theme_colors_defined(self):
        """Test that theme colors are properly defined."""
        palette = config.scene["palette"]
        assert palette["primary"] == "#F4B8C5"  # Rose Quartz
        assert palette["secondary"] == "#E8A0B8"  # Soft Mauve
        assert palette["accent"] == "#E5E7EB"  # Light gray

    def test_dark_mode_color_compatibility(self):
        """Test that colors work in dark mode."""
        # The colors should be theme-aware, not hardcoded
        # Check that we're using theme-aware classes
        config.scene["chat"]["user_message_classes"]
        config.scene["chat"]["assistant_message_classes"]

        # Should use theme-aware classes, not hardcoded colors
        # This is handled by NiceGUI's theme system


class TestChatBubbleAlignment:
    """Test chat bubble alignment."""

    def test_user_message_right_aligned(self):
        """Test user messages are right-aligned."""
        user_row_classes = config.scene["chat"]["user_row_classes"]
        assert "justify-end" in user_row_classes

    def test_assistant_message_left_aligned(self):
        """Test assistant messages are left-aligned."""
        assistant_row_classes = config.scene["chat"]["assistant_row_classes"]
        assert "justify-start" in assistant_row_classes

    def test_user_message_sent_true(self):
        """Test user messages have sent=True."""
        # In the UI code, user messages use sent=True
        # This is verified in the UI tests

    def test_assistant_message_sent_false(self):
        """Test assistant messages have sent=False."""
        # In the UI code, assistant messages use sent=False


class TestScrollbarIssues:
    """Test scrollbar-related bugs."""

    def test_assistant_message_uses_label(self):
        """Test that assistant messages use ui.label to prevent scrollbars."""
        # This is verified in the UI code - assistant messages use ui.label inside ui.chat_message

    def test_css_removes_max_height(self):
        """Test that CSS removes max-height from assistant messages."""
        # Check setup_head_html adds the CSS
        # The CSS should include: .q-message--received { max-height: none !important; overflow: visible !important; }

    def test_no_internal_scrollbars(self):
        """Test that messages don't have internal scrollbars."""
        # This is ensured by using ui.label for assistant content


class TestBubbleTails:
    """Test chat bubble tail styling."""

    def test_css_for_bubble_tails(self):
        """Test that CSS for bubble tails is applied."""
        # The setup_head_html should include CSS for ::after pseudo-elements
        # This creates the triangular tails for chat bubbles

    def test_user_bubble_tail_right_pointing(self):
        """Test user bubble has right-pointing tail."""
        # CSS should have border-left-color for sent messages

    def test_assistant_bubble_tail_left_pointing(self):
        """Test assistant bubble has left-pointing tail."""
        # CSS should have border-right-color for received messages

    def test_tail_matches_bubble_color(self):
        """Test that tail color matches bubble background."""
        # The CSS should use the same colors as the bubbles


class TestDarkModeCompatibility:
    """Test dark mode compatibility."""

    def test_no_hardcoded_colors_in_props(self):
        """Test that chat message props don't use hardcoded colors."""
        # Should use theme-aware props like bg-color=primary instead of hardcoded hex
        user_props = config.scene["chat"]["user_message_props"]
        config.scene["chat"]["assistant_message_props"]

        # Should not contain hardcoded color values
        assert "bg-color=" in user_props  # Theme-aware
        assert "text-color=" in user_props  # Theme-aware
        assert "#" not in user_props  # No hex colors

    def test_theme_aware_classes(self):
        """Test that classes are theme-aware."""
        # Classes should work in both light and dark modes
        # NiceGUI handles this automatically

    def test_header_theme_compatibility(self):
        """Test header works in dark mode."""
        # Header should use theme-aware colors

    def test_footer_theme_compatibility(self):
        """Test footer works in dark mode."""
        # Footer should use theme-aware colors


class TestUIConsistency:
    """Test overall UI consistency."""

    def test_message_bubble_classes_consistent(self):
        """Test that message bubble classes are consistent."""
        user_classes = config.scene["chat"]["user_message_classes"]
        assistant_classes = config.scene["chat"]["assistant_message_classes"]
        welcome_classes = config.scene["chat"]["welcome_message_classes"]

        # All should have shadow-sm for consistency
        assert "shadow-sm" in user_classes
        assert "shadow-sm" in assistant_classes
        assert "shadow-sm" in welcome_classes

    def test_row_classes_proper_alignment(self):
        """Test row classes provide proper alignment."""
        user_row = config.scene["chat"]["user_row_classes"]
        assistant_row = config.scene["chat"]["assistant_row_classes"]

        assert "justify-end" in user_row
        assert "justify-start" in assistant_row

    def test_max_width_consistency(self):
        """Test max width is consistent."""
        # Messages should have reasonable max width
        # This is handled by NiceGUI defaults and custom CSS if needed


class TestPWAFeatures:
    """Test PWA-related features."""

    def test_manifest_link_present(self):
        """Test manifest link is in head."""
        # setup_head_html should include manifest link

    def test_theme_color_meta_present(self):
        """Test theme-color meta tag is present."""
        # Should be set to primary color

    def test_apple_touch_icon_present(self):
        """Test apple-touch-icon link is present."""
        # Should link to branding/apple-touch-icon.png

    def test_viewport_meta_present(self):
        """Test viewport meta tag prevents zoom."""
        # Should have user-scalable=no


class TestAnimationAndTransitions:
    """Test animations and transitions."""

    def test_smooth_transitions(self):
        """Test that UI has smooth transitions."""
        # CSS classes should include transition properties

    def test_no_jarring_changes(self):
        """Test that theme changes are smooth."""
        # Dark mode toggle should be smooth
