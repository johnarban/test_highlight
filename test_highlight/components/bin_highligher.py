import numpy as np
import plotly.graph_objects as go
from plotly.basedatatypes import BaseTraceType
from plotly.callbacks import Points, InputDeviceState
from typing import Callable, Optional

from .BinManager import BinManager

class BinHighlighter(BinManager):
    """
    Example:
        ```python
        from your_module import BinHighlighter

        # Assuming 'viewer' is an instance of a viewer with a plotly figure
        self.bin_highlighter = BinHighlighter(viewer,
                                           line_color='rgba(120, 120, 255, 1)',
                                           fill_color='rgba(0,0,0,.5)',
                                           visible_bins=False, # don't overlay all bins
                                           show_bins_with_data_only=False,
                                           use_selection_layer=True,
                                           setup_selection_layer=False # assume glue plots all have a selection layer
                                           )


        # Setup bin highlighting
        bin_highlighter.setup_bin_highlight()

        # To turn off bin highlighting
        bin_highlighter.turn_off_bin_highlight()
        ```

        JAL
    """

    def __init__(
        self,
        viewer,
        only_show = False,
        on_hover_callback: Optional[Callable] = None,
        on_unhover_callback: Optional[Callable] = None,
        fill_color: str = "rgba(126,126,126,0.5)",
        line_color: str = "white",
        line_width: float = 1.0,
        use_selection_layer: bool = True,
        bin_width: float = 1.0,
        selection_bin_width: float = 1.0,
        show_bins_with_data_only: bool = False,
        visible_bins: bool = False,
        setup_selection_layer: bool = False,
        highlight_on_click: bool = False
    ):
        """
        Initialize the BinHighlighter.

        This class manages the highlighting of bins in a Plotly viewer, optionally integrating
        with a selection layer for enhanced interactivity.

        Parameters
        ----------
        viewer : object
            The viewer object that contains the Plotly figure. This is required for accessing
            the figure's state and layers.
        on_hover_callback : Callable, optional
            Function to call when a bin is hovered over. It should accept parameters
            `(trace, points, state)`. Default is None.
        on_unhover_callback : Callable, optional
            Function to call when a bin is no longer hovered over. It should accept parameters
            `(trace, points, state)`. Default is None.
        fill_color : str, optional
            The color used to fill highlighted bins. Accepts a string in any CSS color format
            (e.g., "rgba(126,126,126,0.5)"). Default is "rgba(126,126,126,0.5)".
        line_color : str, optional
            The color of the line around highlighted bins. Accepts a string in any CSS color
            format. Default is "white".
        line_width : float, optional
            The width of the line around highlighted bins. Default is 1.0.
        use_selection_layer : bool, optional
            Indicates whether to use the selection layer for highlighting. Default is True.
            If False, the bar layer is used, and clicks won't be captured by the selection layer.
        bin_width : float, optional
            The width of each bin. Default is 1.0, affecting how wide the highlight appears.
        selection_bin_width : float, optional
            The width of the selection bins. Default is 1.0. This is used when the selection
            layer is active.
        show_bins_with_data_only : bool, optional
            If True, only bins that contain data will be shown. This helps in focusing on
            relevant data points. Default is False.
        nearest_in_bin : bool, optional
            When True, only highlights the bin currently under the cursor without snapping to
            the nearest bin unless it contains data. Default is True.
        visible_bins : bool, optional
            If True, displays all bins with a black outline, useful for debugging purposes.
            Default is False.
        setup_selection_layer : bool, optional
            If True, sets up the necessary hover and click modes for the selection layer.
            This should be used when the selection layer isn't already configured. Default is False.
        """
        super().__init__(viewer,
                            bin_width=bin_width,
                            selection_bin_width=selection_bin_width,
                            show_bins_with_data_only=show_bins_with_data_only,
                            visible_bins=visible_bins,
                            use_selection_layer=use_selection_layer,
                            )
        self.setup_bin_layer()
        
        
        # self.viewer = viewer
        self.enabled = False

        self.hover_callbacks = [on_hover_callback] if on_hover_callback is not None else []
        self.unhover_callbacks = [on_unhover_callback] if on_unhover_callback is not None else []

        

        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
        
        # I don't know if all viewers with histograms have 
        # a selection layer. I think, but just in case
        if use_selection_layer and not hasattr(viewer, 'selection_layer'):
            raise AttributeError(f'Can not setup the selection layer as viewer {viewer} has no selection layer')
        
        
        self.highlight_on_click = highlight_on_click
        self.only_show = only_show
        
        self._setup_selection_layer = setup_selection_layer


    def clear_callbacks(self):
        """Clear all hover and unhover callbacks"""
        self.hover_callbacks = []
        self.unhover_callbacks = []

    def _create_hover_trace(self, x: float = 0) -> go.Bar | None:
        if self.dx is None:
            raise ValueError('Hover trace creation failed: dx is None')
        return go.Bar(
            name="hover_trace",
            meta="hover_trace_meta",
            x=[self.nearest_bin(x)],
            y=[self.ymax * 1.2 if self.ymax is not None else self.ymax],
            width=self.dx * self.bin_width,
            marker={"color": self.fill_color, "line": {"color": self.line_color, "width": self.line_width}},
            hoverinfo="skip",
            zorder=0,
            visible=False,
            showlegend=False,
        )
    
    

    def setup_bin_highlight(self, on_hover_callback: Optional[Callable] = None) -> None:
        """
        Setup the bin highlighting.

        Args:
            on_hover_callback: Optional callback to be called on hover.
        """
        if self.only_show:
            self.enabled = True
            return
        
        if self.use_selection_layer and not hasattr(self.viewer, "selection_layer"):
            raise AttributeError(f'Can not setup the selection layer as viewer {self.viewer} has no selection layer')

        if self.bins is None or self.dx is None:
            return

        

        # Add the trace to be shown on hover
        self.viewer.figure.add_trace(self._create_hover_trace())

        # append user supplied callback
        if on_hover_callback is not None:
            self.hover_callbacks.append(on_hover_callback)
        
        if self.use_selection_layer:
            if self._setup_selection_layer:
                self.setup_selection_layer()
            if self.highlight_on_click:
                self.viewer.selection_layer.on_click(self._on_hover)
            else:
                self.viewer.selection_layer.on_hover(self._on_hover)
                self.viewer.selection_layer.on_unhover(self._on_unhover)
        
        
        if self.visible_bins or not self.use_selection_layer:
            bin_layer = self.bin_layer
            if not self.use_selection_layer and bin_layer is not None:
                bin_layer.on_hover(self._on_hover)
                bin_layer.on_unhover(self._on_unhover)

        self.enabled = True

    

    def setup_selection_layer(self):
        if not hasattr(self.viewer, 'selection_layer'):
            raise AttributeError(f'Can not setup the selection layer as viewer {self.viewer} has not selection layer')
        resolution = 200
        def new_update_selection(viewer=self.viewer):
            state = viewer.state
            x0 = state.x_min
            dx = (state.x_max - state.x_min) * (1/resolution)
            y0 = state.y_min
            dy = (state.y_max - state.y_min) * 2
            viewer.selection_layer.update(x0=x0 - dx, dx=dx, y0=y0, dy=dy)

        self.viewer.figure.update_layout(clickmode="event", hovermode="closest", showlegend=False)
        self.viewer.selection_layer.update(visible=True, z=[list(range(resolution + 1))], opacity=0, coloraxis="coloraxis")
        self.viewer.figure.update_coloraxes(showscale=False)
        new_update_selection()
        self.viewer._update_selection_layer_bounds = new_update_selection

    @property
    def highlight_trace(self) -> Optional[go.Bar]:
        return next(self.viewer.figure.select_traces({"meta": "hover_trace_meta"}), None)

    
    def _on_hover(self, trace: BaseTraceType, points: Points, state: InputDeviceState) -> None:
        if len(points.xs) > 0:  # hover condition
            if self.highlight_trace:  # hover condition
                self.highlight_trace.x = [self.nearest_bin(points.xs[0])]
                self.highlight_trace.visible = True
                # run hover callbacks
                if self.hover_callbacks is not None:
                    for callback in self.hover_callbacks:
                        callback(trace, points, state)

    def _on_unhover(self, trace: BaseTraceType, points: Points, state: InputDeviceState) -> None:
        if len(points.xs) == 0:  # unhover condition
            if self.highlight_trace:
                self.highlight_trace.visible = False
                if self.unhover_callbacks is not None:
                    # run unhover callbacks
                    for callback in self.unhover_callbacks:
                        callback(trace, points, state)
    
    def turn_on_bin_highlight(self):
        if self.enabled:
            return
        self.setup_bin_highlight()

    
    def turn_off_bin_highlight(self):
        if self.highlight_trace:
            traces_to_keep = lambda t: t != self.highlight_trace
            self.viewer.figure.data = tuple(
                filter(traces_to_keep, self.viewer.figure.data)
            )

        self.turn_off_bins()

        if hasattr(self.viewer, "selection_layer"):
            self.viewer.selection_layer._hover_callbacks = [cb for cb in self.viewer.selection_layer._hover_callbacks if cb != self._on_hover]
            self.viewer.selection_layer._unhover_callbacks = [cb for cb in self.viewer.selection_layer._unhover_callbacks if cb != self._on_unhover]

        self.enabled = False
        
    def show_hide_all_bins(self, show = None):
        if self.bin_layer is None: return
        if show is None:
            self.bin_layer.visible = not self.bin_layer.visible
        else:
            self.bin_layer.visible = show
    
    def set_visible_bin_width(self, width: float):
        self.selection_bin_width = width
        self.redraw()
        
    def redraw(self):
        """Redwaw the bin highlight"""
        if self.enabled:
            self.turn_off_bin_highlight()
            # self.setup_bin_layer()
            self.redraw_bins()
            self.setup_bin_highlight()