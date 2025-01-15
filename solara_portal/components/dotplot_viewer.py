from random import randint

import solara
from glue.core import Data
from reacton import ipyvuetify as rv

from hubbleds.viewers.hubble_dotplot import HubbleDotPlotView, HubbleDotPlotViewer
from cosmicds.viewers.dotplot.state import DotPlotViewerState

from glue.viewers.common.viewer import Viewer
from glue_plotly.viewers.common import PlotlyBaseView
from cosmicds.utils import vertical_line_mark, extend_tool
from hubbleds.utils import PLOTLY_MARGINS
from hubbleds.viewer_marker_colors import LIGHT_GENERIC_COLOR
from itertools import chain
from uuid import uuid4
from plotly.graph_objects import Scatter, Bar
import plotly.graph_objects as go
from numbers import Number
from typing import Callable, Iterable, List, cast, Union, Optional
from solara.toestand import Reactive
import numpy as np

@solara.component
def DotplotViewer(
    gjapp, 
    data=None, 
    component_id=None, 
    title = None, 
    height=300, 
    on_click_callback = None, 
    line_marker_at: Optional[Reactive | int | float] = None, 
    line_marker_color = LIGHT_GENERIC_COLOR, 
    vertical_line_visible: Union[Reactive[bool], bool] = True,
    unit: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    zorder: Optional[list[int]] = None,
    ):
    
    """
    DotplotViewer component
    
    Basic Usage:
    ```python
    data = Data(label = "Test Data", x=[randint(1, 10) for _ in range(30)])
    DotplotViewer(data = data, component_id: str = 'x')
    ```
    
    Parameters:
    - `gjapp`: The GlueJupyter application instance
    - `data`: The data to be displayed in the viewer. Can be a single Data object or a list of Data objects.
    - `component_id`: The component id of the data to be displayed. Only used if `data` is a list of Data objects.
       the components should already linked. component_id is the id for the first (only) Data object in the list.
    - `title`: The title of the viewer
    - `height`: The height of the viewer (default: 400)
    - `on_click_callback`: A callback function that is called when a point is clicked. The function should accept the
    - `line_marker_at`: The value at which the vertical line marker should be placed (passed value is displayed)
    - `line_marker_color`: The color of the vertical line marker (default: 'red')
    - `vertical_line_visible`: Whether the vertical line marker should be visible (default: True)
    - `unit`: The unit for the x-axis values, used in the label for the vertical line (default: None)
    - `x_label`: x_label (Optional[str]): The label for the x-axis of the dot plot. If None, the label will be the name of the x attribute.
    - `y_label`: y_label (Optional[str]): The label for the y-axis of the dot plot. If None, the label will be the name of the y attribute.
    
    """
    
    line_marker_at = solara.Reactive(line_marker_at)
    vertical_line_visible = solara.Reactive(vertical_line_visible)
    
    with rv.Card() as main:
        with rv.Toolbar(dense=True, class_="toolbar"):
            with rv.ToolbarTitle():
                title_container = rv.Html(tag="div")

            rv.Spacer()
            toolbar_container = rv.Html(tag="div")

        viewer_container = rv.Html(tag="div", style_=f"width: 100%; height: {height}px", class_="mb-4")
        
        def _line_ids_for_viewer(viewer: PlotlyBaseView):
            line_ids = []
            traces = list(chain(l.traces() for l in viewer.layers))
            for trace in viewer.figure.data:
                if trace not in traces and isinstance(trace, Scatter) and getattr(trace, "meta", None):
                    line_ids.append(trace.meta)

            return line_ids
        
        def _remove_lines(viewers: List[PlotlyBaseView], line_ids: List[List[str]]):
            for (viewer, viewer_line_ids) in zip(viewers, line_ids):
                lines = list(viewer.figure.select_traces(lambda t: t.meta in viewer_line_ids))
                viewer.figure.data = list(reversed([t for t in viewer.figure.data if t not in lines]))
        
        
        def _add_vertical_line(viewer: PlotlyBaseView, value: Number, color: str, label: str = None, line_ids: list[str] = []):
            print("adding line")
            line = vertical_line_mark(viewer.layers[0], value, color, label = label)
            line_id = str(uuid4())
            line["meta"] = line_id
            line_ids.append(line_id)
            
            viewer.figure.add_trace(line)
            
        
            

        def _add_viewer():
            if data is None:
                viewer_data = Data(label = "Test Data", x=[randint(1, 10) for _ in range(30)])
                gjapp.data_collection.append(viewer_data)
            else: 
                if isinstance(data, Data):
                    viewer_data = data
                elif isinstance(data, list):
                    viewer_data = data[0]
            
            dotplot_view: HubbleDotPlotViewer = gjapp.new_data_viewer(
                HubbleDotPlotView, data=viewer_data, show=False)

            
            if component_id is not None:
                dotplot_view.state.x_att = viewer_data.id[component_id]
            
            if isinstance(data, list):
                if len(data) > 1:
                    for viewer_data in data[1:]:
                        dotplot_view.add_data(viewer_data)
            
            for layer in dotplot_view.layers:
                for trace in layer.traces():
                    trace.update(hoverinfo="skip", hovertemplate=None)

            for layer in dotplot_view.layers:
                original_update_data = layer._update_data
                def no_hover_update():
                    original_update_data()
                    for trace in layer.traces():
                        trace.update(hoverinfo="skip", hovertemplate=None)
                layer._update_data = no_hover_update
            

            # override the default selection layer
            def new_update_selection(self=dotplot_view):
                state = cast(DotPlotViewerState, self.state)
                x0 = state.x_min
                dx = (state.x_max - state.x_min) * .005
                y0 = state.y_min
                dy = (state.y_max - state.y_min) * 2
                self.selection_layer.update(x0=x0 - dx, dx=dx, y0=y0, dy=dy)

            dotplot_view._update_selection_layer_bounds = new_update_selection

            if x_label is not None:    
                dotplot_view.state.x_axislabel = x_label

            if y_label is not None:    
                dotplot_view.state.y_axislabel = y_label

            
            line_ids = [] #[_line_ids_for_viewer(dotplot_view)]
            
            def _update_lines(value = None):
                # remove any pre existing lines

                _remove_lines([dotplot_view], line_ids)
                
                line_ids.clear()
                
                if vertical_line_visible.value and value is not None:
                    _add_vertical_line(dotplot_view, value, line_marker_color, label = "Line Marker", line_ids = line_ids)
                
                # line_ids.append(_line_ids_for_viewer(dotplot_view))
            
            
            
            if title is not None:
                dotplot_view.state.title = title
    
            title_widget = solara.get_widget(title_container)
            title_widget.children = (dotplot_view.state.title or "DOTPLOT VIEWER",)

            toolbar_widget = solara.get_widget(toolbar_container)
            toolbar_widget.children = (dotplot_view.toolbar,)

            viewer_widget = solara.get_widget(viewer_container)
            viewer_widget.children = (dotplot_view.figure_widget,)

            # The auto sizing in the plotly widget only works if the height
            #  and width are undefined. First, unset the height and width,
            #  then enable auto sizing.
            dotplot_view.figure_widget.update_layout(height=None, width=None)
            dotplot_view.figure_widget.update_layout(autosize=True, height=height)
            dotplot_view.figure_widget.update_layout(
                margin=PLOTLY_MARGINS,
                showlegend=False,
                hovermode="x",
                spikedistance=-1,
                xaxis=dict(
                    spikecolor="black",
                    spikethickness=1,
                    spikedash="solid",
                    spikemode="across",
                    spikesnap="cursor",
                    showspikes=True,
                    tickformat=",.0f",
                    titlefont_size=16,
                ),
                yaxis=dict(
                    tickmode="auto",
                    titlefont_size=16,
                ),
            )
            
            def on_click(trace, points, selector):
                print('Dotplot clicked')
                if len(points.xs) > 0:
                    value = points.xs[0]
                    _update_lines(value = value)
                    if on_click_callback is not None:
                        on_click_callback(trace, points, selector)
                else:
                   print("No points selected")

                
                
            dotplot_view.figure.update_layout(clickmode="event", hovermode="closest", showlegend=False)
            dotplot_view.selection_layer.on_click(on_click)
            unit_str = f" {unit}" if unit else ""
            dotplot_view.selection_layer.update(hovertemplate=f"%{{x:,.0f}}{unit_str}<extra></extra>")
            dotplot_view.set_selection_active(True)
            # special treatment for go.Heatmap from https://stackoverflow.com/questions/58630928/how-to-hide-the-colorbar-and-legend-in-plotly-express-bar-graph#comment131880779_68555667
            dotplot_view.selection_layer.update(visible=True, z = [list(range(201))], opacity=0, coloraxis='coloraxis')
            dotplot_view.figure.update_coloraxes(showscale=False)
            
            def add_hover_items():
                bin_edges = dotplot_view.state.bins
                ymax = dotplot_view.state.y_max
                
                x = (bin_edges[0:-1] + bin_edges[1:]) / 2
                dx = bin_edges[1] - bin_edges[0]
                y = np.zeros_like(x) + ymax
                
                hover_trace = Bar(
                    name='hover_trace',
                    meta='hover_trace_meta',
                    x=x,
                    y=y,
                    width=dx,
                    # marker=dict(color='red', opacity=0),
                    hoverinfo='skip'
                )
                
                dotplot_view.figure.add_trace(hover_trace)
                
                # print(dotplot_view.layers)
            
            add_hover_items()

            def apply_zorder():
                #enumerate dotplot_view.layers
                if zorder:
                    print("Applying zorder")
                    for i, layer in enumerate(dotplot_view.layers):
                        layer.state.zorder = zorder[i]
                        print(f"Layer {layer} zorder: {layer.state.zorder}")
            
            def extend_the_tools():  
                print("Extending the tools")       
                extend_tool(dotplot_view, 'plotly:home', activate_cb=apply_zorder)
                extend_tool(dotplot_view, 'hubble:wavezoom', deactivate_cb=apply_zorder)
            extend_the_tools()
            tool = dotplot_view.toolbar.tools['plotly:home']
            if tool:
                tool.activate()
            

            
            
            if line_marker_at.value is not None:
                _update_lines(value = line_marker_at.value)
                
            line_marker_at.subscribe(lambda new_val: _update_lines(value = new_val))
            vertical_line_visible.subscribe(lambda new_val: _update_lines())

            def cleanup():
                for cnt in (title_widget, toolbar_widget, viewer_widget):
                    cnt.children = ()

                for wgt in (dotplot_view.toolbar, dotplot_view.figure_widget):
                    # wgt.layout.close()
                    wgt.close()

            return cleanup

        solara.use_effect(_add_viewer, dependencies=[])

    return main
