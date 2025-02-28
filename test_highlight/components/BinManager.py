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
    ):
        self.viewer = viewer
        self.bin_width = bin_width
        self.selection_bin_width = selection_bin_width
        self.only_show_with_data = show_bins_with_data_only
        self.visible_bins = visible_bins
        self.traces_added = False
        self.bins = None
        self.dx = None
        self.ymax = None
        
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
        return go.Bar(
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
            marker_style = {"color": "rgba(0,0,0,0)", "line": {"color": "rgba(0,0,0,1)"}}
        
        if self.visible_bins or not self.use_selection_layer:
            self.viewer.figure.add_trace(self._create_bin_layer(marker_style = marker_style))

        self.traces_added = True
        
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
        if self.bin_layer is not None:
            self.turn_off_bins()
        sleep(0.1)
        self.setup_bin_layer()
    
    def set_visible_bin_width(self, width: float):
        self.selection_bin_width = width
        self.redraw_bins()