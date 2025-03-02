import numpy as np
import plotly.graph_objects as go
from plotly.basedatatypes import BaseTraceType
from plotly.callbacks import Points, InputDeviceState
from typing import Callable, Optional
from time import sleep
from cosmicds.utils import debounce

class BinManager:
    """Base class for managing histogram bins"""
    def __init__(
        self,
        viewer,
        bin_width: float = 1.0,
        selection_bin_width: float = 1.0,
        show_bins_with_data_only: bool = False,
        visible_bins: bool = True,
        use_selection_layer: bool = True,
        on_click: Optional[Callable] = None,
        on_hover: Optional[Callable] = None,
        on_unhover: Optional[Callable] = None,
        make_bins: bool = True,
    ):
        self.viewer = viewer
        self.bin_width = bin_width
        self.selection_bin_width = selection_bin_width
        self.only_show_with_data = show_bins_with_data_only
        self.visible_bins = visible_bins
        self.make_bins = make_bins
        self.traces_added = False
        self.bins = None
        self.dx = None
        self.ymax = None
        
        self.on_click = on_click
        self.on_hover = on_hover
        self.on_unhover = on_unhover
        
        # I don't know if all viewers with histograms have 
        # a selection layer. I think, but just in case
        if not hasattr(viewer, 'selection_layer'):
            self.use_selection_layer = False
        else:
            self.use_selection_layer = use_selection_layer

    def _calculate_bins(self):
        # Copy existing bin calculation logic
        bin_edges = self.viewer.state.bins
        if bin_edges is None:
            return
        self.bins = (bin_edges[0:-1] + bin_edges[1:]) / 2
        self.dx = bin_edges[1] - bin_edges[0]
        print("finding dx", self.dx)
        self.ymax = self.viewer.state.y_max
    
    def _filter_bins(self):
        if self.bins is None: return
        
        keep = np.full_like(self.bins, False, dtype=bool)
        for layer in self.viewer.state.layers:
            if hasattr(layer, "histogram"):
                data = layer.histogram[1]
                keep = keep | (data > 0)
        bins = self.bins[keep]
        self.bins = bins
        
    def _create_bin_layer(self, marker_style) -> go.Bar | None:
        if self.dx is None or self.bins is None:
            raise ValueError("Bin layer creation failed: Bins or dx is None")
        bar = go.Bar(
                name="all_bins",
                meta="all_bins_meta",
                x=self.bins,
                y=[self.ymax * 1.2 if self.ymax is not None else self.ymax] * len(self.bins),
                width=self.dx * self.selection_bin_width,
                marker=marker_style,
                hoverinfo="skip" if self.use_selection_layer else None,  # must capture the hover. skip will not work
                zorder=1000,
                visible=True,
                showlegend=False,
            )
        return bar
    
    def nearest_bin(self, x: float) -> float | None:
        if self.bins is None:
            return x
        nearest = self.bins[np.argmin(np.abs(x - self.bins))]
        if np.abs(x - nearest) > self.dx:
            return None
        else:
            return nearest

    def setup_bin_layer(self):
        print("Setting up bins")
        self._calculate_bins()
        if self.bins is None or self.dx is None:
            return

        if self.only_show_with_data:
            self._filter_bins()
            
        if self.visible_bins:
            marker_style = {"color": "rgba(0,0,0,0)", "line": {"color": "rgba(0,0,0,1)"}}
        else:
            marker_style = {"color": "rgba(0,0,0,0)", "line": {"color": "rgba(0,0,0,0)"}}
        
        if self.make_bins or not self.use_selection_layer:
            self.viewer.figure.add_trace(self._create_bin_layer(marker_style = marker_style))

        self.traces_added = True
        

        self.setup_selection_layer()
        if not self.use_selection_layer:
            bin_layer = self.bin_layer
            if bin_layer:
                print('adding callbacks')
                bin_layer.on_click(self.on_click)
                bin_layer.on_hover(self.on_hover)
                bin_layer.on_unhover(self.on_unhover)
    
    
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
        self.viewer.set_selection_active(True)
        self.viewer.figure.update_layout(clickmode="event", hovermode="closest", showlegend=False)
        self.viewer.selection_layer.update(visible=True, z=[list(range(resolution + 1))], opacity=0, coloraxis="coloraxis")
        self.viewer.figure.update_coloraxes(showscale=False)
        new_update_selection()
        self.viewer._update_selection_layer_bounds = new_update_selection
        self.reset_selection_layer()
    
    def reset_selection_layer(self):
        self.viewer.set_selection_active(True)
        self.viewer.selection_layer.update(visible=True, z=[list(range(201))], opacity=0, coloraxis="coloraxis")
        self.viewer.figure.update_coloraxes(showscale=False)
        
    def add_callbacks_to_selection_layer(self):
        if hasattr(self.viewer, "selection_layer"):
            if self.on_click:
                self.viewer.selection_layer.on_click(self.on_click)
            if self.on_hover:
                self.viewer.selection_layer.on_hover(self.on_hover)
            if self.on_unhover:
                self.viewer.selection_layer.on_unhover(self.on_unhover)
                
    def remove_callbacks_from_selection_layer(self):
        if hasattr(self.viewer, "selection_layer"):
            self.viewer.selection_layer._click_callbacks = [cb for cb in self.viewer.selection_layer._click_callbacks if cb != self.on_click]
            self.viewer.selection_layer._hover_callbacks = [cb for cb in self.viewer.selection_layer._hover_callbacks if cb != self.on_hover]
            self.viewer.selection_layer._unhover_callbacks = [cb for cb in self.viewer.selection_layer._unhover_callbacks if cb != self.on_unhover]

    
    @property
    def bin_layer(self) -> Optional[go.Bar]:
        return next(self.viewer.figure.select_traces({"meta": "all_bins_meta"}), None)
    
    def turn_off_bins(self):
        if self.bin_layer:
            traces_to_keep = lambda t: t != self.bin_layer and getattr(t, "meta", None) != "all_bins_meta"
            self.viewer.figure.data = tuple(filter(traces_to_keep, self.viewer.figure.data))
            self.traces_added = False
    
    @debounce(.1)
    def redraw_bins(self):
        self.turn_off_bins()
        self.setup_bin_layer()
    
    def set_visible_bin_width(self, width: float):
        self.selection_bin_width = width
        self.redraw_bins()