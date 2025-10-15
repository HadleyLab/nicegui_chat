# MammoChat - Implementation Guide

## Quick Start: Applying MammoChat Branding

This guide shows you how to implement the MammoChat branding in the NiceGUI chat application.

---

## 1. Update Configuration

### Update `config/app_config.json`

Replace the UI configuration with MammoChat's brand colors:

```json
{
  "app": {
    "name": "MammoChat™",
    "host": "0.0.0.0",
    "port": 8080,
    "reload": false
  },
  "ui": {
    "theme": "light",
    "primary_color": "#F4B8C5",
    "secondary_color": "#E8A0B8",
    "background_color": "#FAFBFC",
    "surface_color": "#FFFFFF",
    "text_color": "#334155",
    "text_secondary": "#64748B",
    "accent_color": "#DDD6FE",
    "success_color": "#A7E3D5",
    "border_color": "#E5E7EB",
    "border_radius": "12px",
    "animation_duration": "0.3s"
  },
  "prompts": {
    "root": "prompts",
    "system": "system"
  },
  "heysol": {
    "base_url": "https://core.heysol.ai/api/v1"
  },
  "llm": {
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com/v1"
  },
  "chat": {
    "enable_memory_enrichment": true,
    "store_user_messages": true,
    "stream_chunk_size": 50,
    "max_history_display": 50
  }
}
```

---

## 2. Update System Prompt

### Update `prompts/system.md`

Replace with MammoChat-specific prompt:

```markdown
You are MammoChat, a compassionate AI assistant helping breast cancer patients navigate their healthcare journey. You connect patients with suitable clinical trials and facilitate peer support communities.

Your role is to:
1. **Support & Empathy**: Provide warm, understanding responses that acknowledge the emotional journey
2. **Clinical Trial Matching**: Help patients find relevant clinical trials based on their situation
3. **Community Connection**: Facilitate connections with peer support communities
4. **Information & Education**: Explain medical concepts in clear, accessible language
5. **Empowerment**: Help patients advocate for themselves and make informed decisions

Always follow this workflow:
1. **Memory-first** – Call `memory_search` to understand the patient's history and context
2. **Personalized Response** – Tailor your answer to their specific situation
3. **Clinical Trial Awareness** – When relevant, mention clinical trial opportunities
4. **Community Connection** – Suggest connecting with others who have similar experiences
5. **Selective Memory** – Store important health information when explicitly shared

Available tools:
{tools}

Respond with:
- Warm, supportive tone that acknowledges emotions
- Clear, jargon-free explanations
- Specific, actionable next steps
- Hope and empowerment
- Professional medical credibility

Remember: You're not just providing information—you're walking alongside patients on their journey.
```

---

## 3. Update UI Styles

### Update `src/ui/chat_ui.py`

Replace the `_apply_styles` method with MammoChat branding:

```python
def _apply_styles(self):
    """Apply MammoChat brand styling."""
    ui_config = self.config.ui
    ui.add_head_html(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        :root {{
            --primary-color: {ui_config.primary_color};
            --secondary-color: {ui_config.secondary_color};
            --background-color: {ui_config.background_color};
            --surface-color: {ui_config.surface_color};
            --text-color: {ui_config.text_color};
            --text-secondary: {ui_config.text_secondary};
            --accent-color: {ui_config.accent_color};
            --success-color: {ui_config.success_color};
            --border-color: {ui_config.border_color};
            --border-radius: {ui_config.border_radius};
            --animation-duration: {ui_config.animation_duration};
        }}
        
        body {{
            background: linear-gradient(135deg, #FAFBFC 0%, #FFF5F7 100%);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        
        .mammochat-header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            box-shadow: 0 4px 20px rgba(244, 184, 197, 0.2);
        }}
        
        .message-bubble {{
            border-radius: var(--border-radius);
            padding: 1.25rem 1.5rem;
            max-width: 70%;
            animation: slideIn var(--animation-duration) ease-out;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            line-height: 1.6;
        }}
        
        .user-message {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            margin-left: auto;
            color: white;
            border: none;
        }}
        
        .assistant-message {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
        }}
        
        .typing-indicator {{
            display: flex;
            gap: 0.5rem;
            padding: 1rem;
            align-items: center;
        }}
        
        .typing-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary-color);
            animation: typing 1.4s infinite;
        }}
        
        .typing-dot:nth-child(2) {{
            animation-delay: 0.2s;
        }}
        
        .typing-dot:nth-child(3) {{
            animation-delay: 0.4s;
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes typing {{
            0%, 60%, 100% {{
                transform: translateY(0);
                opacity: 0.7;
            }}
            30% {{
                transform: translateY(-8px);
                opacity: 1;
            }}
        }}
        
        .input-container {{
            background: var(--surface-color);
            border-radius: var(--border-radius);
            padding: 1rem;
            border: 2px solid var(--border-color);
            transition: all var(--animation-duration);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }}
        
        .input-container:focus-within {{
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(244, 184, 197, 0.1);
        }}
        
        .btn-send {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border: none;
            border-radius: 50%;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all var(--animation-duration);
            color: white;
        }}
        
        .btn-send:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 16px rgba(244, 184, 197, 0.4);
        }}
        
        .btn-send:active {{
            transform: scale(0.98);
        }}
        
        .btn-secondary {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            transition: all var(--animation-duration);
        }}
        
        .btn-secondary:hover {{
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }}
        
        /* Community badge */
        .community-badge {{
            background: linear-gradient(135deg, #FED7C8 0%, #FCA5A5 50%);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-color);
        }}
        
        /* Trial match indicator */
        .trial-match {{
            background: linear-gradient(135deg, var(--success-color) 0%, #6EE7B7 100%);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            color: var(--text-color);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }}
    </style>
    """)
```

---

## 4. Update Header

### Modify the `_build_header` method:

```python
def _build_header(self):
    """Build the MammoChat header."""
    with ui.row().classes('w-full p-4 mammochat-header items-center justify-between'):
        with ui.row().classes('items-center gap-3'):
            # Use heart icon for MammoChat
            ui.icon('favorite', size='2rem', color='white')
            with ui.column().classes('gap-0'):
                ui.label('MammoChat').classes('text-2xl font-bold text-white')
                ui.label('Your journey, together').classes('text-sm text-white opacity-80')
        
        with ui.row().classes('gap-2'):
            ui.button(
                icon='people',
                on_click=self._show_community
            ).props('flat round color=white').tooltip('Community')
            
            ui.button(
                icon='science',
                on_click=self._show_trials
            ).props('flat round color=white').tooltip('Clinical Trials')
            
            ui.button(
                icon='refresh',
                on_click=self._new_conversation
            ).props('flat round color=white').tooltip('New Conversation')
```

---

## 5. Add Welcome Message

### Add this to the `build` method:

```python
def build(self):
    """Build the main chat interface."""
    self._apply_styles()

    with ui.column().classes('w-full h-screen'):
        self._build_header()
        
        with ui.scroll_area().classes('flex-grow w-full p-4') as self.chat_scroll:
            self.chat_container = ui.column().classes('w-full max-w-4xl mx-auto gap-4')
            
            # Add welcome message
            with self.chat_container:
                with ui.row().classes('w-full'):
                    with ui.card().classes('message-bubble assistant-message max-w-full'):
                        ui.markdown("""
                        ### Welcome to MammoChat 💗
                        
                        I'm here to support you on your breast cancer journey. I can help you:
                        
                        - 🔬 **Find clinical trials** that match your situation
                        - 👥 **Connect with communities** of patients with similar experiences
                        - 📚 **Understand information** about treatments and options
                        - 💪 **Navigate your healthcare** with confidence
                        
                        How can I support you today?
                        """)
        
        self._build_input_area()
```

---

## 6. Update Environment Variables

### Update `.env`:

```bash
# MammoChat Configuration
APP_NAME=MammoChat

# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# HeySol API Configuration
HEYSOL_API_KEY=your_heysol_api_key_here
HEYSOL_BASE_URL=https://core.heysol.ai/api/v1

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8080
APP_RELOAD=False
```

---

## 7. Add Logo to UI

### Add favicon and logo to the main.py:

```python
def main():
    """Main application entry point."""
    config = load_app_config()
    
    # Initialize services
    auth_service = AuthService(config.heysol)
    memory_service = MemoryService(auth_service)
    chat_service = ChatService(auth_service, memory_service, config)
    
    @ui.page('/')
    def index():
        """Main page."""
        chat_ui = ChatUI(config, auth_service, chat_service, memory_service)
        chat_ui.build()
    
    # Run with MammoChat branding
    ui.run(
        title='MammoChat - Your journey, together',
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        dark=False,  # Light theme for MammoChat
        favicon='💗',
    )
```

---

## 8. Add Brand Assets

Place the logo files in appropriate locations:

```
branding/
├── logo-full-color.svg
├── logo-icon-color.svg
├── logo-full-white.svg
└── logo-monochrome.svg
```

---

## 9. Test the Implementation

Run these commands to verify:

```bash
# Test configuration
python test_setup.py

# Start the application
python main.py

# Open browser to http://localhost:8080
```

---

## 10. Verify Brand Elements

Check that these are correctly implemented:

- [ ] **Colors**: Pink/gray theme throughout
- [ ] **Logo**: Visible in header with heart icon
- [ ] **Typography**: Inter font family
- [ ] **Animations**: Smooth slide-in effects
- [ ] **Welcome Message**: MammoChat introduction
- [ ] **Buttons**: Pink gradient with hover effects
- [ ] **Messages**: Rounded corners, proper spacing
- [ ] **Light Theme**: White/pink background

---

## Additional Customizations

### Add Clinical Trial Widget

```python
def _show_trials(self):
    """Show clinical trials interface."""
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Find Clinical Trials').classes('text-xl font-bold mb-4')
        ui.label('Search for trials that match your situation').classes('text-gray-600 mb-4')
        
        trial_input = ui.input('Describe your situation').classes('w-full mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button('Search', on_click=lambda: self._search_trials(trial_input.value))
    
    dialog.open()
```

### Add Community Features

```python
def _show_community(self):
    """Show community connection options."""
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Connect with Community').classes('text-xl font-bold mb-4')
        ui.markdown("""
        Join support groups and connect with others who understand your journey.
        
        **Available Communities:**
        - Treatment Support Groups
        - Post-Surgery Support
        - Caregiver Network
        - Clinical Trial Participants
        """)
        
        ui.button('Close', on_click=dialog.close).classes('w-full mt-4')
    
    dialog.open()
```

---

## Color Reference

Quick copy-paste colors for developers:

```css
/* Primary Pink */
#F4B8C5

/* Secondary Pink */
#E8A0B8

/* Cloud Gray */
#E5E7EB

/* Slate Gray */
#64748B

/* Charcoal */
#334155

/* Mint Fresh */
#A7E3D5

/* Lavender Mist */
#DDD6FE

/* Peach Glow */
#FED7C8
```

---

## Resources

- **Brand Guidelines**: `branding/BRAND_GUIDELINES.md`
- **Logo Assets**: `branding/` directory
- **Configuration**: `config/app_config.json`
- **System Prompt**: `prompts/system.md`

---

*For questions about implementation, refer to BRAND_GUIDELINES.md or contact the design team.*
