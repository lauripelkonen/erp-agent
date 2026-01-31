# ERP Agents Design System Documentation

## Color Palette

### Brand Colors
- **Primary Purple**: `rgba(38,0,255,0.8)` - Used for primary CTAs, user input areas, and brand highlights
- **Black**: `#000000` - Primary text color, navigation buttons
- **White**: `#ffffff` - Text on dark backgrounds, card backgrounds
- **Gray**: `#6f6f6f` - Secondary text, process steps

### Background Colors
- **Main Gradient**: `bg-gradient-to-b from-[#ededed] to-[#ffffff]` - Main page background
- **Button Gradient**: `bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a]` - Primary button styling
- **Card Backgrounds**: 
  - `bg-[#ffffff99]` (white with 60% opacity) - Main content cards
  - `bg-[rgba(255,255,255,0.1)]` - Process step containers
  - `bg-[rgba(0,0,0,0.02)]` - Secondary button background

### Transparency System
- **High Transparency**: `0.1` (10%) - Subtle overlays
- **Medium Transparency**: `0.4` (40%) - Text de-emphasis
- **Strong Transparency**: `0.7` (70%) - Secondary text
- **Card Transparency**: `0.6` (60% via `99` hex) - Card backgrounds

## Typography System

### Font Family
- **Primary Font**: `'Inter:Medium', sans-serif` - Used throughout the interface
- **Font Variants**: 
  - `'Inter:Regular'` for body text
  - `'Inter:Medium'` for headings and emphasis

### Font Sizes & Hierarchy
- **Hero Heading**: `text-[40px]` - Main page title
- **Section Headings**: `text-[15px]` - Navigation, card titles
- **Body Text**: `text-[13px]` - Button text, secondary content
- **Small Text**: `text-[12px]` - Process steps, metadata
- **Micro Text**: `text-[10.5px]` - User input text

### Font Weights
- **Normal**: `font-normal` (400) - Body text
- **Medium**: `font-medium` (500) - Most interface elements, headings

### Letter Spacing (Tracking)
- **Tight**: `tracking-[-1.6px]` - Large headings (40px)
- **Medium Tight**: `tracking-[-0.6px]` - Standard interface text (15px)
- **Standard Tight**: `tracking-[-0.52px]` - Button text (13px)

### Line Height
- **Normalized**: `leading-[normal]` - Used for most text elements
- **Zero**: `leading-[0]` - Tight spacing for interface elements

## Spacing and Layout System

### Base Spacing Unit
- **Base Unit**: `--spacing: 0.25rem` (4px)

### Common Spacing Values
- **Extra Small**: `gap-1` = 4px
- **Small**: `gap-1.5` = 6px
- **Medium**: `gap-2.5` = 10px
- **Large**: `gap-4` = 16px
- **Extra Large**: `gap-6` = 24px
- **XXL**: `gap-9` = 36px

### Padding System
- **Button Padding**: 
  - Small: `px-4 py-1.5` (16px, 6px)
  - Large: `px-6 py-3` (24px, 12px)
- **Container Padding**: `px-8` (32px) for main content areas

### Positioning System
- **Centered Containers**: `left-1/2 transform -translate-x-1/2` - Horizontal centering
- **Max Width Container**: `max-w-7xl` (80rem) - Content container width
- **Absolute Positioning**: Extensive use of `absolute` with precise pixel values

## Button Styles and Interactions

### Primary Button (CTA)
```css
className="bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] px-6 py-3 rounded-[36px] shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200"
```
- **Background**: Dark gradient from gray to black
- **Border Radius**: 36px (fully rounded)
- **Padding**: 24px horizontal, 12px vertical
- **Shadow**: Multi-layered shadow system
- **Hover Effect**: Enhanced shadow on hover with 200ms transition

### Secondary Button
```css
className="bg-[rgba(0,0,0,0.02)] px-6 py-3 rounded-[36px] border border-[rgba(0,0,0,0.1)]"
```
- **Background**: Very light black (2% opacity)
- **Border**: Light gray border
- **Text Color**: `rgba(0,0,0,0.7)` (70% black)

### Navigation Button
```css
className="bg-black px-4 py-1.5 rounded-[36px]"
```
- **Background**: Solid black
- **Text**: White
- **Smaller padding**: 16px horizontal, 6px vertical

## Shadow System

### Card Shadows
- **Primary Card**: `shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)]`
- **Process Container**: `shadow-[1.5px_3px_31.35px_-9px_rgba(0,0,0,0.25)]`
- **User Input**: `shadow-[1.5px_3px_16.8px_-6px_rgba(0,0,0,0.25)]`
- **Process Steps**: `shadow-[0px_1.5px_8.25px_-3px_rgba(0,0,0,0.25)]`

### Button Shadows
- **Primary Button Default**: `shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)]`
- **Primary Button Hover**: `shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)]`

## Border Radius System

- **Full Rounded**: `rounded-[36px]` - Buttons
- **Large Rounded**: `rounded-[25.5px]` - Main cards
- **Medium Rounded**: `rounded-[13.5px]` - Process containers, user inputs
- **Small Rounded**: `rounded-[7.5px]` - Process steps

## Component Positioning and Layout

### Container Strategy
- **Centered Layout**: All major sections use `left-1/2 max-w-7xl transform -translate-x-1/2 w-full px-8`
- **Absolute Positioning**: Extensive use of absolute positioning for precise control
- **Z-Index Management**: Uses `z-10` for ensuring proper layering

### Responsive Approach
- **Max Width Container**: `max-w-7xl` (1280px) with `px-8` padding
- **Percentage-based Width**: `w-full` for full-width within containers
- **Fixed Pixel Values**: Many components use precise pixel positioning

### Flexbox Patterns
- **Standard Flex**: `flex items-center justify-start` or `justify-between`
- **Content Stretch**: `content-stretch` for maintaining content width
- **Gap System**: Consistent use of gap utilities (`gap-2.5`, `gap-4`, `gap-6`)

## Transform and Animation System

### Transform Utilities
- **Translation**: `transform -translate-x-1/2` for centering
- **Complex Transforms**: `rotate-[10deg] skew-x-[9.851deg]` for card effects
- **Scale and Rotate**: `rotate-[348.255deg] scale-x-[104.42%] skew-x-[348deg]` for decorative elements

### Transition System
- **Shadow Transitions**: `transition-shadow duration-200` for button hovers
- **Duration**: 200ms as standard duration for interactions

## CSS Custom Properties Usage

### Core Variables
- `--spacing: 0.25rem` - Base spacing unit
- `--font-sans` - Default font family
- `--color-black: #000` - Primary black
- `--color-white: #fff` - Primary white

### Text Size Variables
- `--text-xs: 0.75rem`
- `--text-sm: 0.875rem`
- `--text-base: 1rem`
- `--text-lg: 1.125rem`

## Implementation Guidelines

### Creating New Components

1. **Use the established color palette** - Stick to the defined brand colors and transparency levels
2. **Follow spacing conventions** - Use the --spacing variable and established gap patterns
3. **Maintain typography hierarchy** - Use Inter font with established size and weight combinations
4. **Apply consistent shadows** - Use the multi-layered shadow system for depth
5. **Use rounded corners consistently** - Follow the established radius system (7.5px, 13.5px, 25.5px, 36px)
6. **Center content properly** - Use the established centering pattern with max-width containers

### Button Creation Pattern
```jsx
// Primary CTA Button
<button className="bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] px-6 py-3 rounded-[36px] text-white font-medium text-[15px] tracking-[-0.6px] shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200">
  Button Text
</button>

// Secondary Button
<button className="bg-[rgba(0,0,0,0.02)] border border-[rgba(0,0,0,0.1)] px-6 py-3 rounded-[36px] text-[rgba(0,0,0,0.7)] font-medium text-[15px] tracking-[-0.6px]">
  Button Text
</button>
```

### Card Creation Pattern
```jsx
<div className="bg-[#ffffff99] rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-6">
  Card Content
</div>
```

This design system ensures consistency across the application and provides clear guidelines for creating new components that match the existing aesthetic and functionality.