# MammoChat - Quick Reference Card

## 🚀 Application Status
✅ **Running:** http://localhost:8080

## 💗 Key Features

### Dark Mode Toggle
- **Light Mode:** Shows `dark_mode` icon (moon)
- **Dark Mode:** Shows `light_mode` icon (sun)
- Single button toggle with automatic icon switching

### Color Scheme
**Light Mode:**
- Background: Soft pink gradient (#FAFBFC → #F9F5F6)
- Header: White (#FFFFFF)
- User Messages: Pink gradient (#F4B8C5 → #E8A0B8)
- Assistant Messages: White cards with slate text

**Dark Mode:**
- Background: Dark blue gradient (#0f172a → #1e293b)
- Header: Dark slate (#1e293b)
- User Messages: Same pink gradient (maintains brand)
- Assistant Messages: Dark slate cards (#1e293b)

## 🎯 User Actions

### Chat
- **Send Message:** Type and press Enter or click send button
- **New Conversation:** Click refresh icon
- **Toggle Dark Mode:** Click sun/moon icon

### Notifications
- ✅ Success: Green (top-right)
- ⚠️ Warning: Orange (top)
- ❌ Error: Red (top, 5 seconds)
- ℹ️ Info: Blue (top-right)

## 🛠️ Technical Stack

### Pure NiceGUI
- No custom CSS (except Google Fonts)
- All Tailwind utility classes
- Quasar component props
- Native dark mode API

### Backend
- **LLM:** DeepSeek (via Pydantic AI 1.0+)
- **Memory:** HeySol API
- **Framework:** NiceGUI 2.24+
- **Python:** 3.9+

## 🎨 Brand Identity

**Name:** MammoChat
**Tagline:** Your journey, together
**Icon:** 💗 Favorite/Heart
**Primary Color:** Rose Quartz (#F4B8C5)
**Purpose:** Breast cancer patient support

## 📱 Responsive Design
- Desktop: Full layout with sidebar potential
- Mobile: Stacked layout, touch-friendly buttons
- Tablet: Optimized message width (70% max-width)

## 🔒 Security
- API keys in .env file
- Secure HeySol authentication
- No sensitive data in frontend

## 📊 Performance
- Streaming responses (real-time)
- Lazy loading of chat history
- Optimized scroll behavior
- Minimal re-renders

## 🎓 Code Quality
- Type hints throughout
- Async/await patterns
- Error boundaries
- Clean separation of concerns

## 🌟 What's New (v2.0)
1. Single dark mode toggle (was 2 buttons)
2. Icon switching (light_mode ↔ dark_mode)
3. Fixed header dark mode styling
4. Pure NiceGUI patterns (no custom CSS)
5. Toast notifications for all actions
6. Fixed agent generation error
7. Better error handling
8. Improved UX with visual feedback

---

**Ready to help patients beat breast cancer together!** 💗🚀
