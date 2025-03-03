# Histogram Bin Highlighting Methods

This document describes the two histogram bin highlighting methods available in the CosmicDS library: Python-based highlighting (`BinHighlighter`) and JavaScript-based highlighting (`PlotlyHighlighting`).

## Overview of Highlighting Methods

### Python-based Highlighting (BinHighlighter)
- Implemented using Python callbacks and Plotly traces
- Provides detailed control over bin appearance and behavior
- Emits both hover and click events to Python callbacks
- Built on top of the `BinManager` base class

### JavaScript-based Highlighting (PlotlyHighlighting)
- Implemented using Vue.js for client-side highlighting
- Uses `BinManager` to create the underlying bins, then applies highlighting in the browser
- Generally more performant since highlighting happens entirely in the browser
- Only emits click events (no hover events) back to Python
- Uses DOM manipulation to apply highlighting styles directly to bins created by `BinManager`

## Comparison Matrix

| Feature | Python-based (BinHighlighter) | JavaScript-based (PlotlyHighlighting) |
|---------|-------------------------------|---------------------------------------|
| **Implementation** | Python callbacks + Plotly traces | Vue.js + DOM manipulation |
| **Underlying Bins** | Created by `BinManager` | Created by `BinManager` |
| **Hover Events** | ✅ Sent to Python callbacks | ❌ Handled in JavaScript only |
| **Click Events** | ✅ Sent to Python callbacks | ✅ Sent to Python callbacks |
| **Performance** | Moderate (requires Python processing) | High (client-side only) |
| **Bin Visibility** | Configurable with `visible_bins` | Configurable with `visible_bins` |
| **Data-only Bins** | ✅ Supported via `show_bins_with_data_only` | ✅ Supported via `BinManager` |

## Option Details

### Python-based Highlighting Options (BinHighlighter)

| Option | Description | Default | Effect |
|--------|-------------|---------|--------|
| `visible_bins` | Show outlines for all bins | `False` | When `True`, all bins have visible outlines |
| `show_bins_with_data_only` | Only show bins containing data | `False` | When `True`, empty bins are hidden |
| `use_selection_layer` | Use selection layer for interactions | `True` | When `True`, uses selection layer; otherwise uses bar layer |
| `bin_width` | Width of highlighted bin | `1.0` | Controls width of highlighting |
| `selection_bin_width` | Width of selection bins | `1.0` | Controls width when selection layer is active |
| `fill_color` | Color to fill highlighted bins | `"rgba(126,126,126,0.5)"` | Sets highlight fill color |
| `line_color` | Color of highlighted bin outline | `"white"` | Sets highlight outline color |
| `line_width` | Width of highlighted bin outline | `1.0` | Sets highlight outline width |
| `highlight_on_click` | Highlight bins on click instead of hover | `False` | When `True`, highlighting triggers on click |

### JavaScript-based Highlighting Options (PlotlyHighlighting)

| Option | Description | Default | Effect |
|--------|-------------|---------|--------|
| `show` | Show debug controls | `False` | When `True`, shows debugging buttons |
| `highlight` | Enable highlighting | `True` | When `False`, disables all highlighting |
| `debug` | Show debug info if elements not found | `False` | When `True`, shows controls if elements not found |
| `visible_bins` | Show outlines for all bins | `False` | When `True`, all bins have visible outlines |
| `fillColor` | Color to fill highlighted bins | `"rgba(0, 0, 0)"` | Sets highlight fill color |
| `fillOpacity` | Opacity of fill color | `0.5` | Controls fill transparency |
| `strokeColor` | Color of highlighted bin outline | `"rgba(255, 120, 255, 1)"` | Sets highlight outline color |
| `strokeOpacity` | Opacity of outline | `1` | Controls outline transparency |
| `strokeWidth` | Width of highlighted bin outline | `1` | Sets highlight outline width |

## Selection Layer Explained

The `use_selection_layer` option determines how mouse interactions are captured and processed, with significant differences in behavior between Python and JavaScript highlighting methods.

### What is the Selection Layer?
- The selection layer is an invisible overlay covering the entire plot area
- It captures mouse events (clicks and hovers) independently from the visible bars
- When enabled, it allows for continuous interaction across the entire plot, not just over bars

### How `use_selection_layer` Affects Each Highlighting Method

#### Python Highlighting (`BinHighlighter`)

| `use_selection_layer` | Hover Events | Click Events |
|-----------------------|--------------|--------------|
| `True` | Work continuously across the entire plot; report continuous location values | Work continuously across the entire plot; report continuous location values |
| `False` | Only work over bars; report bar locations | Work everywhere but report bar locations when over bars and continuous values elsewhere |

#### JavaScript Highlighting (`PlotlyHighlighting`)

| `use_selection_layer` | Hover Events | Click Events |
|-----------------------|--------------|--------------|
| `True` | Never sent to Python (handled in JavaScript) | Work continuously across the entire plot; report continuous location values |
| `False` | Never sent to Python (handled in JavaScript) | Work on bars and continuous areas but report bar locations when over bars |

### Technical Implementation Details
- **With selection layer (`True`)**: Mouse events are captured by an invisible overlay that spans the entire plot area. This provides smoother, continuous interaction.
- **Without selection layer (`False`)**: Mouse events are captured directly by the bar elements themselves, which can make interaction less consistent but may be more accurate for precisely selecting specific bars.

### When to Use Each Option:

- **Use selection layer (`True`) when**:
  - You want continuous hover/click information across the entire plot
  - You need to capture events between bars
  - You're working with dense histograms where precise bar selection might be difficult

- **Don't use selection layer (`False`) when**:
  - You want hover/click events to work only directly over bars
  - You want events to report the actual bar values rather than continuous values
  - You're implementing custom interaction logic that requires direct bar interaction

## Event Callbacks

### Python-based Highlighting (BinHighlighter)

| Callback | Description | When Fired |
|----------|-------------|------------|
| `on_hover_callback` | Called when hovering over a bin | When cursor moves over a bin |
| `on_unhover_callback` | Called when no longer hovering | When cursor leaves a bin |
| `on_click_callback` | Called when clicking a bin | When a bin is clicked |

### JavaScript-based Highlighting (PlotlyHighlighting)

| Callback | Description | When Fired |
|----------|-------------|------------|
| Selection layer click | Provided by Plotly selection layer | When a bin is clicked |
| Hover events | Not available | N/A (handled internally in JavaScript) |

## Usage in TestViewer

The `TestViewer` component provides a unified interface for both highlighting methods:

```python
TestViewer(gjapp, 
           data=data,
           highlight_bins=True,    
           show_bins_with_data_only=False, 
           use_selection_layer=True,
           on_click_callback=my_click_handler, 
           on_hover_callback=my_hover_handler,
           nbins=15,
           bin_width=1.0,
           use_python_highlighing=True  # Switch to False for JavaScript-based highlighting
           )
```

### TestViewer Configuration Impact

| Option | Value | Python Highlighting | JavaScript Highlighting |
|--------|-------|---------------------|-------------------------|
| `use_python_highlighing` | `True` | BinHighlighter used | Not used |
| `use_python_highlighing` | `False` | Not used | PlotlyHighlighting used |
| `highlight_bins` | `True` | Bins are highlighted | Bins are highlighted |
| `highlight_bins` | `False` | No highlighting | No highlighting |
| `show_bins_with_data_only` | `True` | Only bins with data shown | Only bins with data shown |
| `visible_bins` | `True` | All bins have visible outlines | All bins have visible outlines |
| `use_selection_layer` | `True` | Uses selection layer | Uses selection layer |
| `use_selection_layer` | `False` | Uses bar layer | Uses bar layer |
| `on_hover_callback` | Function | Called on hover | Not called (no hover events) |
| `on_click_callback` | Function | Called on click | Called on click |
| `nbins` | Integer | Controls number of bins | Controls number of bins |
| `bin_width` | Float | Controls bin width | Controls bin width |

## Example Configurations

### For maximum interactivity with hover events
```python
TestViewer(gjapp, data=data,
           highlight_bins=True,
           use_python_highlighing=True,
           on_hover_callback=my_hover_handler)
```

### For best performance with large datasets
```python
TestViewer(gjapp, data=data,
           highlight_bins=True,
           use_python_highlighing=False)
```

### For debugging bin placement
```python
TestViewer(gjapp, data=data,
           highlight_bins=True,
           use_python_highlighing=True,
           visible_bins=True,
           show_bins_with_data_only=False)
```

---

**Note**: The JavaScript-based highlighting method (`PlotlyHighlighting`) does not emit hover events to Python, which means hover callbacks won't be triggered. However, it generally provides better performance, especially for large datasets. Both highlighting methods rely on the `BinManager` class to create and manage the underlying histogram bins.

**Generated by Copilot**
