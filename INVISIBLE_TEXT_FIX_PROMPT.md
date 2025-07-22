# SchoolDriver Modern: Invisible Text Fix Prompt

## Problem Analysis
The SchoolDriver Modern application has widespread invisible text issues caused by:

1. **CSS Variable Conflicts**: Multiple color systems with inconsistent variable names
2. **Legacy CSS Inheritance**: Old CSS rules with `visibility: hidden` affecting text
3. **Bootstrap Override Issues**: Dark theme colors being overridden by Bootstrap defaults
4. **Missing Color Fallbacks**: CSS variables not defined in all contexts
5. **Chart.js Text Color Problems**: Graph text invisible on dark backgrounds

## Required Fixes

### 1. Standardize CSS Color Variables
**File: `schooldriver-modern/templates/base.html`**

Replace the existing `:root` variables section with a unified color system:

```css
:root {
    /* Unified Dark Theme Color System */
    --bg-primary: #0D1117;
    --bg-secondary: #161B22;
    --bg-tertiary: #21262D;
    --bg-card: #2d2d2d;
    --bg-input: #404040;
    
    /* Text Colors */
    --text-primary: #E6EDF3;
    --text-secondary: #7D8590;
    --text-muted: #656D76;
    --text-light: #E6EDF3;
    --text-dark: #1a1a1a;
    
    /* Accent Colors */
    --accent-primary: #1E88E5;
    --accent-teal: #14b8a6;
    --accent-teal-hover: #0d9488;
    --accent-success: #10B981;
    --accent-warning: #F59E0B;
    --accent-danger: #EF4444;
    
    /* Border Colors */
    --border-primary: #30363D;
    --border-secondary: #21262D;
    --border-muted: #404040;
}
```

### 2. Force Text Visibility Across All Elements
Add these critical CSS rules to ensure text is never invisible:

```css
/* Force Text Visibility - Critical Fix */
body, body * {
    color: var(--text-primary, #E6EDF3) !important;
}

/* Override any invisible text rules */
.hidden-text,
code[style*="visibility: hidden"],
*[style*="visibility: hidden"] {
    visibility: visible !important;
    display: inline !important;
    color: var(--text-primary) !important;
}

/* Ensure all text elements are visible */
h1, h2, h3, h4, h5, h6, p, span, div, td, th, li, a, label {
    color: var(--text-primary, #E6EDF3) !important;
    opacity: 1 !important;
}

/* Fix specific Bootstrap overrides */
.text-muted {
    color: var(--text-secondary, #7D8590) !important;
}

.text-white {
    color: #ffffff !important;
}
```

### 3. Fix Dashboard and Chart Text Visibility
**File: `schooldriver-modern/static/css/dashboard.css`**

Add at the top of the file:

```css
/* Emergency Text Visibility Fix */
.dashboard-content,
.dashboard-content *,
.chart-container,
.chart-container * {
    color: var(--text-primary) !important;
}

/* Chart.js Text Color Fix */
canvas {
    color: var(--text-primary) !important;
}
```

### 4. Fix Authentication Pages
**File: `schooldriver-modern/static/css/auth.css`**

Add these overrides:

```css
/* Auth Page Text Visibility */
.auth-content,
.auth-content *,
.admin-auth-container,
.admin-auth-container * {
    color: var(--admin-text-primary, #e0e0e0) !important;
}

/* Form Text Visibility */
input, textarea, select, label {
    color: var(--admin-text-primary) !important;
}

input::placeholder,
textarea::placeholder {
    color: var(--admin-text-secondary, #b0b0b0) !important;
}
```

### 5. Fix Portal-Specific Text Issues
For each portal template (`student_portal`, `parent_portal`), add:

```css
/* Portal Text Visibility Fix */
.portal-content,
.portal-content *,
.nav-link,
.card-body,
.list-group-item {
    color: var(--text-primary, #E6EDF3) !important;
}

/* Message Text Visibility */
.message-item,
.message-item * {
    color: var(--text-primary) !important;
}
```

### 6. Legacy CSS Override
**File: `schooldriver/static_files/css/style.css`**

Comment out or override problematic rules:

```css
/* DISABLE PROBLEMATIC VISIBILITY RULES */
code {
    /* position: absolute; visibility: hidden; */
    position: static !important;
    visibility: visible !important;
    color: var(--text-primary, #E6EDF3) !important;
}

label.inline-label-has-text {
    /* visibility: hidden !important; */
    visibility: visible !important;
    color: var(--text-primary, #E6EDF3) !important;
}
```

### 7. Admin Panel Text Fix
**File: `schooldriver-modern/templates/admin/base_site.html`**

Add these fixes to the dark mode styles:

```css
/* Admin Panel Text Visibility */
body.dark-mode,
body.dark-mode * {
    color: #E6EDF3 !important;
}

body.dark-mode .form-row label,
body.dark-mode .field-box label,
body.dark-mode th,
body.dark-mode td {
    color: #E6EDF3 !important;
}
```

### 8. Chart.js Text Color Fix
**File: `schooldriver-modern/templates/dashboard.html`**

Update the Chart.js configuration:

```javascript
// Enhanced Chart.js Dark Theme Setup
function setupChartDefaults() {
    // Force all chart text to be visible
    Chart.defaults.color = '#E6EDF3';
    Chart.defaults.font = { color: '#E6EDF3' };
    
    // Override any potential invisible text
    if (Chart.defaults.plugins?.legend?.labels) {
        Chart.defaults.plugins.legend.labels.color = '#E6EDF3';
    }
    
    // Force axis text visibility
    Chart.defaults.scales = Chart.defaults.scales || {};
    ['category', 'linear', 'x', 'y'].forEach(scale => {
        if (!Chart.defaults.scales[scale]) Chart.defaults.scales[scale] = {};
        if (!Chart.defaults.scales[scale].ticks) Chart.defaults.scales[scale].ticks = {};
        Chart.defaults.scales[scale].ticks.color = '#E6EDF3';
    });
}
```

## Implementation Priority

1. **CRITICAL**: Fix base.html color variables (affects all pages)
2. **HIGH**: Add force visibility CSS rules 
3. **HIGH**: Fix dashboard chart text visibility
4. **MEDIUM**: Update portal-specific styles
5. **LOW**: Clean up legacy CSS conflicts

## Testing Checklist

After implementation, verify text is visible on:
- [ ] Dashboard page (all charts and text)
- [ ] Login/Registration forms
- [ ] Student Portal pages
- [ ] Parent Portal pages  
- [ ] Admin panel pages
- [ ] Public pages
- [ ] All form inputs and labels
- [ ] Navigation menus
- [ ] Tables and lists

## Notes

- Use `!important` sparingly but necessarily for overriding Bootstrap
- Test on both Chrome and Safari for CSS variable support
- Check mobile responsive views
- Verify accessibility contrast ratios remain compliant 