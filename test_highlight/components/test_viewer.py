import solara
import reacton.ipyvuetify as rv

from hubbleds.viewers.hubble_dotplot import HubbleDotPlotView, HubbleDotPlotViewer
from glue.core import Data
import numpy as np
from typing import Callable, Optional, List, cast
from .bin_highligher import BinHighlighter


@solara.component
def TestViewer(gjapp, 
               data: Optional[Data] = None, 
               highlight_bins: solara.Reactive[bool] | bool = False,    
               use_selection_layer: solara.Reactive[bool] | bool = False,
               on_click_callback = None, 
               on_hover_callback = None,
               nbins: solara.Reactive[int] | int = 5,
               bin_width: solara.Reactive[float] | float = 1,):
    """
    A Solara component to create a test viewer with bin highlighting.

    Args:
        gjapp: The Glue Jupyter application object.
        data: Optional Glue Data object.
        highlight_bins: Boolean or reactive value to enable bin highlighting.
        use_selection_layer: Boolean or reactive value to use the selection layer.
        on_click_callback: Optional callback to be called on click.
        on_hover_callback: Optional callback to be called on hover.
        nbins: Integer or reactive value for the number of bins.
    
    Example:
        ```python
        import solara
        from glue.core import Data
        from your_module import TestViewer

        # Create a Glue Jupyter application object
        gjapp = ...

        # Create some data
        data = Data(label='Example Data', x=[1, 2, 3, 4, 5])

        # Create the TestViewer component
        viewer = TestViewer(gjapp, data=data, highlight_bins=True, use_selection_layer=True)

        # Render the viewer in a Solara app
        solara.render(viewer)
        ```
    """
    viewer_container = rv.Html(tag='div', style_=f"width: 100%; height: 100%")
    use_selection_layer = solara.use_reactive(use_selection_layer)
    highlight_bins = solara.use_reactive(highlight_bins)
    bin_highlighter: solara.Reactive[BinHighlighter | None] = solara.use_reactive(None)
    nbins = solara.use_reactive(nbins)
    bin_width = solara.use_reactive(bin_width)

    
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
        bin_highlighter.set(BinHighlighter(viewer, 
                                           on_hover_callback=on_hover_callback,
                                           bin_width=bin_width.value, 
                                            use_selection_layer=use_selection_layer.value,
                                            selection_bin_width=.5,
                                            show_bins_with_data_only=False,
                                            show_all_bins=True,
                                            setup_selection_layer=False
                                           ))

        def toggle_bin_highlight(turn_on: bool):
            if bin_highlighter.value is None:
                return
            if turn_on:
                bin_highlighter.value.setup_bin_highlight()
            else:
                bin_highlighter.value.turn_off_bin_highlight()
        
        toggle_bin_highlight(highlight_bins.value)
        highlight_bins.subscribe(toggle_bin_highlight)      
          
        def on_use_selection_layer(value):
            if bin_highlighter.value is not None:
                bin_highlighter.value.use_selection_layer = value
                bin_highlighter.value.redraw()
        use_selection_layer.subscribe(on_use_selection_layer)
        
        def on_nbins_change(value):
            if bin_highlighter.value is not None:
                bin_highlighter.value.redraw()
        nbins.subscribe(on_nbins_change)
        
        def on_bin_width_change(value):
            if bin_highlighter.value is not None:
                bin_highlighter.value.set_bin_width(value)
        bin_width.subscribe(on_bin_width_change)
        
        def cleanup():
                vc.children = ()
                viewer.figure_widget.close()

        return cleanup


    

    
    solara.use_effect(lambda :_viewer_setup(data), dependencies=[])
    
    
    return viewer_container



