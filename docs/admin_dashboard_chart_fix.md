# SchoolDriver Modern – Admin Analytics Dashboard: Chart Rendering Fix

## Problem Description
The "Applicant Status Distribution" (pie) and "Monthly Admission Trends" (line) canvases were blank, while the two bar charts displayed correctly in the admin analytics dashboard.

## Root Causes Identified
1. Both canvases had **height = 0 px** because their parent `.chart-container` was inside a grid row whose height collapsed after the first canvas renders.
2. In some browsers Chart.js initializes **before** the canvases receive a final layout, so it draws at 0 × 0.
3. Inline JavaScript loading order and timing issues with DOM layout calculation.

## Solution Implemented

### 1. Guaranteed Canvas Height with CSS
Enhanced CSS in `admin_dashboard.html` to ensure containers maintain proper dimensions:

```css
.chart-container {
    min-height: 320px !important;
    height: 320px !important;
    display: flex;
    flex-direction: column;
    /* parent won't collapse */
}

.chart-container canvas {
    width: 100% !important;
    height: 280px !important;   /* Chart.js needs >0 height */
    max-height: 280px !important;
    flex: 1;
}
```

### 2. External JavaScript File Organization
Moved all chart initialization logic from inline to external file `static/js/admin_charts.js`:

- **Better timing control**: Uses `requestAnimationFrame` and `setTimeout` for proper initialization sequence
- **Force canvas dimensions**: Explicitly sets canvas dimensions before Chart.js initialization
- **Modular code**: Separated chart logic from template for better maintainability

### 3. Proper Loading Order
Updated `admin_dashboard.html` script loading:

```html
<script src="{% static 'js/chart.min.js' %}" defer></script>
<script>
  /* exposes data for external JS file */
  window.dashboardData = {{ dashboard_data_json|safe }};
</script>
<script src="{% static 'js/admin_charts.js' %}" defer></script>
```

### 4. Empty Dataset Guards
Added guards in each `buildXChart` helper to handle missing data gracefully:

```javascript
if (!dataset.data.length || dataset.data.every(v => v === 0)) {
     container.innerHTML = '<p class="text-muted text-center mt-5">No data</p>';
     return;
}
```

## Implementation Details

### Files Modified:
- **`templates/admin_dashboard.html`**: Enhanced CSS, refactored JavaScript loading
- **`static/js/admin_charts.js`**: New external chart initialization file

### Key Functions:
- `initializeAdminCharts()`: Main initialization with proper timing
- `forceCanvasDimensions()`: Ensures canvas dimensions before Chart.js init
- `buildPipelineChart()`, `buildDocumentsChart()`, `buildStatusChart()`, `buildTrendsChart()`: Individual chart builders with error handling
- `updateAdminChartsTheme()`: Theme switching support

### Timing Strategy:
1. `DOMContentLoaded` event fires
2. `requestAnimationFrame` ensures CSS layout is applied
3. `forceCanvasDimensions()` explicitly sets container and canvas sizes
4. 150ms delay allows grid layout calculation to complete
5. Individual chart builders initialize with guaranteed dimensions

## Verification Steps

1. **Load `/dashboard/admin/`** → All four charts should appear correctly
2. **Toggle Light/Dark theme** → Colors switch and charts redraw properly
3. **Resize window** → Canvases maintain aspect ratio due to `maintainAspectRatio: false` and fixed height
4. **Empty data handling** → Charts show "No data" message instead of errors

## Technical Benefits

- **Consistent rendering**: Charts always render regardless of browser timing
- **Better performance**: External JS file is cached and loads efficiently
- **Maintainability**: Chart logic is separated from template code
- **Error resilience**: Graceful handling of missing or empty datasets
- **Theme support**: Proper theme switching without re-initialization issues

## Commit Message
```
fix: resolve admin dashboard chart rendering issues

- Add guaranteed canvas height with flexbox layout
- Move chart initialization to external JS file for better timing
- Implement proper loading sequence with requestAnimationFrame
- Add empty dataset guards for all chart types
- Ensure all four charts (pipeline, documents, status, trends) render correctly

Fixes blank pie and line charts in admin analytics dashboard.
```

---

This fix ensures reliable chart rendering across all browsers and provides a robust foundation for the admin analytics dashboard functionality.
