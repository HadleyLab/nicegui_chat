# MammoChat Brand Guidelines

## Brand Identity

**MammoChat** is an AI-powered platform that connects patients with suitable clinical trials and facilitates peer support communities. Our brand embodies trust, innovation, and community in healthcare.

## Brand Values

- 🤝 **Trust**: Reliable, professional, and secure
- 💡 **Innovation**: Cutting-edge AI technology for better outcomes
- 💗 **Empathy**: Compassionate, supportive, and understanding
- 🌸 **Community**: Connected, collaborative, and caring
- 🎯 **Empowerment**: Helping patients take control of their health journey

## Brand Personality

- Warm and approachable, yet professional
- Innovative but not intimidating
- Feminine without being overly decorative
- Modern and clean with soft, comforting elements
- Trustworthy and medically credible

---

## Color Palette

### Primary Colors

**Rose Quartz** (Primary Pink)
- HEX: `#F4B8C5`
- RGB: `rgb(244, 184, 197)`
- Use: Primary brand color, buttons, highlights
- Represents: Compassion, warmth, femininity

**Soft Mauve** (Secondary Pink)
- HEX: `#E8A0B8`
- RGB: `rgb(232, 160, 184)`
- Use: Accents, hover states, secondary elements
- Represents: Care, support, gentleness

### Secondary Colors

**Cloud Gray** (Neutral)
- HEX: `#E5E7EB`
- RGB: `rgb(229, 231, 235)`
- Use: Backgrounds, cards, containers
- Represents: Clarity, simplicity, space

**Slate Gray** (Text)
- HEX: `#64748B`
- RGB: `rgb(100, 116, 139)`
- Use: Body text, secondary information
- Represents: Stability, professionalism

**Charcoal** (Headers)
- HEX: `#334155`
- RGB: `rgb(51, 65, 85)`
- Use: Headlines, important text
- Represents: Authority, trust

### Accent Colors

**Mint Fresh** (Success/Health)
- HEX: `#A7E3D5`
- RGB: `rgb(167, 227, 213)`
- Use: Success messages, health indicators
- Represents: Growth, healing, hope

**Lavender Mist** (Innovation)
- HEX: `#DDD6FE`
- RGB: `rgb(221, 214, 254)`
- Use: AI features, tech elements
- Represents: Innovation, intelligence

**Peach Glow** (Community)
- HEX: `#FED7C8`
- RGB: `rgb(254, 215, 200)`
- Use: Community features, social elements
- Represents: Connection, warmth

### Semantic Colors

**Error/Alert**
- HEX: `#FCA5A5` (Soft Red)
- Use: Error messages, warnings

**Warning**
- HEX: `#FCD34D` (Soft Yellow)
- Use: Caution messages

**Info**
- HEX: `#BAE6FD` (Soft Blue)
- Use: Information messages

---

## Typography

### Primary Font: Inter
- **Headlines**: Inter Bold (700)
- **Subheadings**: Inter SemiBold (600)
- **Body Text**: Inter Regular (400)
- **Captions**: Inter Medium (500)

### Font Sizes

```css
/* Headlines */
h1: 2.5rem (40px) - Bold
h2: 2rem (32px) - SemiBold
h3: 1.5rem (24px) - SemiBold
h4: 1.25rem (20px) - Medium

/* Body */
body: 1rem (16px) - Regular
small: 0.875rem (14px) - Regular
caption: 0.75rem (12px) - Medium
```

### Line Heights
- Headlines: 1.2
- Body text: 1.6
- Captions: 1.4

---

## Logo Specifications

### Logo Variations

1. **Full Logo** (Horizontal)
   - Icon + "MammoChat" text
   - Use: Main marketing materials, headers
   - Minimum width: 120px

2. **Stacked Logo** (Vertical)
   - Icon above "MammoChat" text
   - Use: Mobile apps, square spaces
   - Minimum width: 80px

3. **Icon Only**
   - Stylized heart + chat bubble
   - Use: App icons, favicons, small spaces
   - Minimum size: 32px

4. **Wordmark**
   - "MammoChat" text only
   - Use: Navigation bars, tight spaces
   - Minimum width: 100px

### Logo Elements

**Icon Design:**
- Combines a heart shape with a chat bubble
- Soft, rounded edges for approachability
- Gradient from Rose Quartz to Soft Mauve
- Optional: subtle sparkle/stars for AI innovation

**Wordmark:**
- "Mammo" in Rose Quartz (#F4B8C5)
- "Chat" in Slate Gray (#64748B)
- Clean, modern sans-serif (Inter)

### Clear Space
- Minimum clear space around logo: Equal to the height of the icon
- No other elements within this space

### Logo Don'ts
- ❌ Don't rotate the logo
- ❌ Don't change the colors arbitrarily
- ❌ Don't add effects (drop shadows, outlines)
- ❌ Don't distort or stretch
- ❌ Don't place on busy backgrounds
- ❌ Don't use low-resolution versions

---

## Visual Style

### Design Principles

1. **Soft & Rounded**
   - Border radius: 12px-16px for cards
   - Border radius: 8px for buttons
   - Border radius: 24px for pills/tags
   - No sharp corners

2. **Gentle Gradients**
   - Use subtle gradients (5-10% variation)
   - Direction: Top-left to bottom-right
   - Apply to backgrounds, buttons, highlights

3. **Ample White Space**
   - Don't crowd elements
   - Use generous padding and margins
   - Let content breathe

4. **Soft Shadows**
   - Light, diffused shadows
   - Elevation hierarchy through shadow depth
   - Example: `box-shadow: 0 4px 6px rgba(244, 184, 197, 0.15)`

### Imagery Style

**Photography:**
- Bright, well-lit images
- Warm tones with pink undertones
- Show diverse patients and healthcare professionals
- Genuine, unposed moments preferred
- Focus on hope, strength, and connection

**Illustrations:**
- Line art style with soft curves
- Rose Quartz and Lavender Mist colors
- Simple, friendly, not overly medical
- Show community, support, connection

**Icons:**
- Rounded, friendly style (Lucide or Heroicons)
- Stroke width: 2px
- Consistent sizing
- Use brand colors

---

## UI Components

### Buttons

**Primary Button**
```css
background: linear-gradient(135deg, #F4B8C5 0%, #E8A0B8 100%);
color: white;
border-radius: 8px;
padding: 12px 24px;
box-shadow: 0 2px 4px rgba(244, 184, 197, 0.2);
```

**Secondary Button**
```css
background: #E5E7EB;
color: #334155;
border-radius: 8px;
padding: 12px 24px;
```

**Text Button**
```css
background: transparent;
color: #F4B8C5;
text-decoration: underline;
```

### Cards

```css
background: white;
border-radius: 16px;
padding: 24px;
box-shadow: 0 4px 12px rgba(100, 116, 139, 0.08);
border: 1px solid #E5E7EB;
```

### Input Fields

```css
background: white;
border: 2px solid #E5E7EB;
border-radius: 8px;
padding: 12px 16px;
transition: border-color 0.2s;

/* Focus state */
border-color: #F4B8C5;
box-shadow: 0 0 0 3px rgba(244, 184, 197, 0.1);
```

---

## Animation & Motion

### Timing Functions
- Standard: `ease-out`
- Enter: `cubic-bezier(0.25, 0.46, 0.45, 0.94)`
- Exit: `cubic-bezier(0.55, 0.085, 0.68, 0.53)`

### Durations
- Quick: 150ms (hover, focus)
- Standard: 300ms (buttons, cards)
- Slow: 500ms (page transitions)

### Animation Principles
- Soft, gentle movements
- No jarring or aggressive animations
- Fade + slide combinations
- Subtle scale effects on hover (1.02-1.05)

---

## Voice & Tone

### Writing Style
- **Warm & Supportive**: "We're here with you"
- **Clear & Simple**: Avoid medical jargon
- **Empowering**: Focus on patient agency
- **Hopeful**: Emphasize positive outcomes
- **Professional**: Maintain medical credibility

### Example Copy

**Good:**
- "Find clinical trials that match your journey"
- "Connect with others who understand"
- "Your voice matters in your treatment decisions"

**Avoid:**
- "Search database for trial protocols"
- "Patient cohort matching system"
- "Medical intervention recommendations"

---

## Applications

### Web Application
- Use full horizontal logo in header
- Rose Quartz for primary actions
- Cloud Gray backgrounds
- Generous spacing and padding

### Mobile App
- Use icon or stacked logo
- Touch-friendly button sizes (min 44px)
- Bottom navigation in Cloud Gray
- Active state in Rose Quartz

### Marketing Materials
- Full color logo on light backgrounds
- Use brand photography
- Emphasize community and connection
- Include patient testimonials

### Social Media
- Square icon for profile pictures
- Rose Quartz and Mint Fresh for graphics
- Share patient success stories
- Use #MammoChat hashtag

---

## Accessibility

### Color Contrast
- All text meets WCAG AA standards (4.5:1 for body, 3:1 for large text)
- Rose Quartz on white: Use Charcoal text for readability
- Test all color combinations

### Interactive Elements
- Minimum touch target: 44x44px
- Clear focus indicators
- Support keyboard navigation
- Provide alt text for images

---

## Brand Protection

### Trademark
- MammoChat™ is a trademark
- Use ™ symbol in formal contexts
- Register logo and wordmark

### Usage Rights
- Internal teams: Full access to all brand assets
- Partners: Approved materials only
- Third parties: Written permission required

### Quality Control
- Use only approved logo files
- Don't recreate logos
- Maintain aspect ratios
- Use high-resolution images

---

## Contact

For brand questions or asset requests:
- **Brand Team**: brand@mammochat.com
- **Design System**: Available at design.mammochat.com
- **Asset Library**: assets.mammochat.com

---

*Last Updated: October 2, 2025*
*Version: 1.0*
