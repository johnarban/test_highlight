import solara
import reacton.ipyvuetify as rv

from hubbleds.viewers.hubble_dotplot import HubbleDotPlotView, HubbleDotPlotViewer

import numpy as np

from glue.core import Data

import numpy as np
import plotly.graph_objects as go
from plotly.basedatatypes import BaseTraceType
from plotly.callbacks import Points, InputDeviceState
from typing import Callable, Optional, List, cast



class BinHighlighter:
    def __init__(self, viewer):
        self.viewer = viewer
        self.hover_callback = None
        self.unhover_callback = None
        self.enabled = False
        self.use_selection_layer = True

    def setup_bin_highlight(self,
                            color: str = 'rgba(126,126,126,0.5)',
                            line_color: str | None = 'white',
                            line_width: int = 1,
                            bin_width: float = 0.98,
                            on_hover: Optional[Callable] = None,
                            on_unhover: Optional[Callable] = None,
                            use_selection_layer: bool = True,
                            selection_bin_width: float = 0.98,
                            only_show_with_data: bool = False) -> None:
        if not hasattr(self.viewer, 'selection_layer'):
            return

        bin_edges = self.viewer.state.bins
        ymax = self.viewer.state.y_max

        bins = (bin_edges[0:-1] + bin_edges[1:]) / 2
        dx = bin_edges[1] - bin_edges[0]

        if only_show_with_data:
            keep = np.full_like(bins, False, dtype=bool)
            for layer in self.viewer.state.layers:
                if hasattr(layer, 'histogram'):
                    data = layer.histogram[1]
                    keep = keep | (data > 0)
            bins = bins[keep]

        def nearest_bin(x: float) -> float:
            return bins[np.argmin(np.abs(x - bins))]

        def hover_trace(x: float = 0) -> go.Bar:
            return go.Bar(
                name='hover_trace',
                meta='hover_trace_meta',
                x=[nearest_bin(x)],
                y=[ymax],
                width=dx * bin_width,
                marker={
                    'color': color,
                    'line': {
                        'color': line_color,
                        'width': line_width
                    }
                },
                hoverinfo='skip',
                zorder=0,
                visible=False,
                showlegend=False
            )

        self.viewer.figure.add_trace(hover_trace())

        def on_hover_callback(trace: BaseTraceType, points: Points, state: InputDeviceState) -> None:
            print('Hover')
            if len(points.xs) == 0:
                return
            old_bar = next(self.viewer.figure.select_traces({'meta': 'hover_trace_meta'}))
            if old_bar is not None:
                old_bar.x = [nearest_bin(points.xs[0])]
                old_bar.visible = True
                if on_hover is not None:
                    on_hover(trace, points, state, old_bar)

        def on_unhover_callback(trace: BaseTraceType, points: Points, state: InputDeviceState) -> None:
            print('Unhover')
            if len(points.xs) == 0:
                print('No points')
                old_bar = next(self.viewer.figure.select_traces({'meta': 'hover_trace_meta'}))
                if old_bar is not None:
                    old_bar.visible = False
                    if on_unhover is not None:
                        on_unhover(trace, points, state, old_bar)

        if use_selection_layer:
            self.viewer.selection_layer.on_hover(on_hover_callback)
            self.viewer.selection_layer.on_unhover(on_unhover_callback)
        else:
            bin_layer = go.Bar(
                name='all_bins',
                meta='all_bins_meta',
                x=bins,
                y=[ymax]*len(bins),
                width=dx * selection_bin_width,
                marker={'color': 'rgba(0,0,0,0)', 'line': {'color': 'rgba(0,0,0,1)'}},
                hoverinfo='none',
                zorder=0,
                visible=True,
                showlegend=False
            )
            self.viewer.figure.add_trace(bin_layer)
            bin_layer = next(self.viewer.figure.select_traces({'meta': 'all_bins_meta'}))
            bin_layer.on_hover(on_hover_callback)
            bin_layer.on_unhover(on_unhover_callback)

        self.hover_callback = on_hover_callback
        self.unhover_callback = on_unhover_callback
        self.enabled = True

    def turn_off_bin_highlight(self):
        if not hasattr(self.viewer, 'selection_layer') or self.viewer is None:
            return
        print('Turning off bin highlight')
        bin_layer = next(self.viewer.figure.select_traces({'meta': 'all_bins_meta'}), None)

        if self.hover_callback in self.viewer.selection_layer._hover_callbacks:
            print('Removing hover callback from selection layer')
            index = self.viewer.selection_layer._hover_callbacks.index(self.hover_callback)
            self.viewer.selection_layer._hover_callbacks.pop(index)
            if bin_layer and self.hover_callback in bin_layer._hover_callbacks:
                print('Removing hover callback from bin layer')
                index = bin_layer._hover_callbacks.index(self.hover_callback)
                bin_layer._hover_callbacks.pop(index)
                bin_layer.hoverinfo = 'skip'

        if self.unhover_callback in self.viewer.selection_layer._unhover_callbacks:
            print('Removing unhover callback from selection layer')
            index = self.viewer.selection_layer._unhover_callbacks.index(self.unhover_callback)
            self.viewer.selection_layer._unhover_callbacks.pop(index)
            if bin_layer and self.unhover_callback in bin_layer._unhover_callbacks:
                print('Removing unhover callback from bin layer')
                index = bin_layer._unhover_callbacks.index(self.unhover_callback)
                bin_layer._unhover_callbacks.pop(index)
                bin_layer.hoverinfo = 'skip'

        traces = list(self.viewer.figure.data)
        for trace_meta in ['hover_trace_meta', 'all_bins_meta']:
            trace = next(self.viewer.figure.select_traces({'meta': trace_meta}), None)
            if trace and trace in traces:
                idx = traces.index(trace)
                traces.pop(idx)
        self.viewer.figure.data = tuple(traces)
        self.enabled = False

@solara.component
def TestViewer(gjapp, 
               data: Optional[Data] = None, 
               highlight_bins: solara.Reactive[bool] | bool = False,    
               use_selection_layer: solara.Reactive[bool] | bool = False,
               on_click_callback = None, 
               on_hover_callback = None,
               nbins = 5): #

    viewer_container = rv.Html(tag='div', style_=f"width: 100%; height: 100%")
    use_selection_layer = solara.use_reactive(use_selection_layer)
    highlight_bins = solara.use_reactive(highlight_bins)
    bin_highlighter: solara.Reactive[BinHighlighter | None] = solara.use_reactive(None)
    nbins = solara.use_reactive(nbins)
    callbacks = solara.use_reactive([])
    
    def _viewer_setup(data):
        print('Setting up viewer')
        if data is None:
            if len(gjapp.data_collection) == 0:
                data = Data(label='Dotplot Data', x = list(np.random.normal(0,3, 200)))
                gjapp.data_collection.append(data)
            else:
                data = gjapp.data_collection[0]
        if data not in gjapp.data_collection:
            gjapp.data_collection.append(data)
        
        viewer = gjapp.new_data_viewer(HubbleDotPlotView, data=data, show=True)
        vc = solara.get_widget(viewer_container)
        vc.children = (viewer.figure_widget,) # type: ignore
        
        viewer.state.hist_n_bin = nbins.value
        nbins.subscribe(lambda x: setattr(viewer.state, 'hist_n_bin', x))
        
        def on_click(trace, points, state):
            print(f'on_click at {points}')
            if on_click_callback is not None:
                on_click_callback(trace, points, state)
        
        
        viewer.figure.update_layout(clickmode="event", hovermode="closest", showlegend=False)
        viewer.selection_layer.on_click(on_click)
        
        viewer.selection_layer.update(hovertemplate=f"%{{x:,.3f}}<extra></extra>")
        # viewer.set_selection_active(True)
        # special treatment for go.Heatmap from https://stackoverflow.com/questions/58630928/how-to-hide-the-colorbar-and-legend-in-plotly-express-bar-graph#comment131880779_68555667
        viewer.selection_layer.update(visible=True, z = [list(range(201))], opacity=1, coloraxis='coloraxis')
        viewer.figure.update_coloraxes(showscale=False)
        
        def new_update_selection(self=viewer):
                state = viewer.state
                x0 = state.x_min
                dx = (state.x_max - state.x_min) * (1/200)
                y0 = state.y_min
                dy = (state.y_max - state.y_min) * 2
                self.selection_layer.update(x0=x0 - dx, dx=dx, y0=y0, dy=dy)#, z = [list(range(201))], coloraxis='coloraxis', visible = True)

        viewer._update_selection_layer_bounds = new_update_selection
        new_update_selection()
    
        # Create BinHighlighter instance
        bin_highlighter.set(BinHighlighter(viewer))

        def toggle_bin_highlight(turn_on: bool):
            print('Toggling bin highlight', turn_on)
            if bin_highlighter.value is None:
                return
            if turn_on:
                bin_highlighter.value.setup_bin_highlight(
                    on_hover=on_hover_callback, 
                    bin_width=.3, 
                    use_selection_layer=use_selection_layer.value,
                    selection_bin_width=.3,
                    only_show_with_data=False
                )
            else:
                bin_highlighter.value.turn_off_bin_highlight()
        
        toggle_bin_highlight(highlight_bins.value)
        highlight_bins.subscribe(toggle_bin_highlight)
        def on_use_selection_layer(value: bool):
            if bin_highlighter.value is None:
                return
            if bin_highlighter.value.enabled:
                bin_highlighter.value.turn_off_bin_highlight()
                toggle_bin_highlight(highlight_bins.value)
            else:
                toggle_bin_highlight(highlight_bins.value)
        use_selection_layer.subscribe(on_use_selection_layer)
        
        def cleanup():
                vc.children = ()
                viewer.figure_widget.close()

        return cleanup


    
        

    
    solara.use_effect(lambda :_viewer_setup(data), dependencies=[])
    
    
    return viewer_container



