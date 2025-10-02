# Changelog

All notable changes to MammoChat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-02

### Changed
- **Simplified configuration management**: Only API keys (secrets) remain in `.env` file
- All non-secret configuration moved to `config/app_config.json`
- Removed environment variable overrides for app name, host, port, reload
- Changed favicon from 🤖 to 💗 (heart emoji for MammoChat branding)
- Updated package name from "nicegui-chat" to "mammochat" in `pyproject.toml`

### Added
- Version information system with `src/__version__.py`
- Version display in window title: "MammoChat v0.2.0"
- Version logging on startup: "Starting MammoChat v0.2.0"
- MIT License file

### Documentation
- Updated README with clearer separation of secrets vs. configuration
- Simplified `.env.example` to show only API keys
- Added comprehensive CHANGELOG.md
- Updated all references to reflect MammoChat branding

### Security
- Improved security by removing ability to store secrets in JSON config
- API keys now **must** be in environment variables (`.env` file)
- Clearer separation of concerns: secrets in `.env`, everything else in JSON

## [0.1.0] - 2025-10-02 (Initial MammoChat Release)

### Added - MammoChat Brand & Identity
- Comprehensive MammoChat branding package with 4 SVG logo variants:
  - `logo-full-color.svg` - Primary logo with pink gradient heart and grey chat bubble
  - `logo-icon.svg` - Icon-only version for avatars and small spaces
  - `logo-monochrome.svg` - Single-color charcoal version for print
  - `logo-white.svg` - White version for dark backgrounds
- MammoChat color palette:
  - Primary (Rose Quartz): #F4B8C5
  - Secondary (Soft Mauve): #E8A0B8
  - Chat Bubble Grey: #64748B with 0.15 opacity
  - Charcoal: #334155
- Brand guidelines and implementation documentation in `branding/` directory
- Tagline: "Your journey, together"
- Compassionate welcome message focused on breast cancer support

### Added - Pure NiceGUI Implementation
- Complete rewrite using **only** pure NiceGUI components
- `ui.colors()` API for theme customization (no custom CSS)
- Quasar props (`.props()`) for component behavior
- Quasar/Tailwind classes (`.classes()`) for layout
- Native NiceGUI dark mode with automatic theme adaptation
- Responsive design with Quasar breakpoint classes (`gt-xs`)
- No custom `.style()` inline CSS
- No custom HTML/CSS animations
- No Tailwind `dark:` classes (incompatible with NiceGUI's dark mode)

### Added - Configuration-Driven UI
- All UI text externalized to `config/app_config.json`
- Configurable elements include:
  - Tagline, welcome message, tooltips, notifications
  - Logo paths, placeholder text, button labels
  - Colors, theme settings
- Easy internationalization/localization support
- Simple rebranding without code changes
- A/B testing capability for messaging

### Added - UI Features
- Dark mode toggle with icon switching (light_mode ↔ dark_mode)
- Responsive header with logo and tagline
- User message bubbles with primary color background
- Assistant message bubbles with bordered cards
- Typing indicator with animated dots spinner
- Toast notifications for user feedback
- Logo integration in header and welcome message
- Gradient send button with primary color
- Clean, minimalist design with rounded cards

### Changed
- Application renamed from "NiceGUI Chat" to "MammoChat"
- Default theme changed from dark to light mode
- Primary color changed from indigo (#6366f1) to Rose Quartz (#F4B8C5)
- All hardcoded UI strings moved to configuration
- Logo display system converted to static file serving
- UIConfig class expanded with 16+ new configuration fields

### Fixed
- Dark mode now works correctly with NiceGUI's `body.body--dark` class
- Tagline text cutoff issue resolved by removing custom styling
- Logo contrast improved with subtle 0.15 opacity on chat bubble
- Logo spacing fixed to prevent text overlap ("Chat" now at x=175)
- Logout functionality changed from server shutdown to page reload
- Message bubbles styled consistently with theme colors

### Technical Details
- NiceGUI 2.24.2 with ui.colors() theming API
- Static file serving: `app.add_static_files('/branding', 'branding')`
- Dark mode binding: `ui.dark_mode(value=False)` starting in light mode
- Responsive classes: Quasar `gt-xs` for mobile hiding
- User messages: `bg-primary text-white` classes
- Assistant messages: `bordered` prop with default styling
- Typing indicator: `color='primary'` spinner with label
- All logos: SVG format with proper viewBox and paths

### Documentation
- Updated README.md with MammoChat branding and features
- Added comprehensive branding documentation
- Updated configuration examples
- Added pure NiceGUI implementation notes
- Documented color palette and design system
- Created CHANGELOG.md for version tracking

## [0.1.0] - Initial Release

### Added
- Initial NiceGUI Chat application
- DeepSeek AI integration for chat responses
- HeySol memory management integration
- Pydantic AI agent framework
- Streaming chat responses
- Authentication system
- Memory enrichment for conversations
- Basic UI with dark theme
- Configuration management system
- Service layer architecture (ChatService, AuthService, MemoryService)
- Pydantic models for type safety
- Environment variable support
- Structured logging with structlog
