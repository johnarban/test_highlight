import solara
import reacton.ipyvuetify as rv

from hubbleds.viewers.hubble_dotplot import HubbleDotPlotView, HubbleDotPlotViewer
from glue.core import Data
import numpy as np
from typing import Callable, Optional, List, cast
from .bin_highligher import BinHighlighter
from .BinManager import BinManager
from .PlotlyHighlighting import _PlotlyHighlighting
from hubbleds.utils import PLOTLY_MARGINS


@solara.component
def TestViewer(gjapp, 
               data: Optional[Data] = None, 
               highlight_bins: solara.Reactive[bool] | bool = True,    
               show_bins_with_data_only: solara.Reactive[bool] | bool = False, 
               use_selection_layer: bool = True,
               on_click_callback = None, 
               on_hover_callback = None,
               nbins: solara.Reactive[int] | int = 15,
               bin_width: solara.Reactive[float] | float = 1,
               use_python_highlighing: bool = True
               ):
    """
    A Solara component to create a test viewer with bin highlighting.

    Args:
        gjapp: The Glue Jupyter application object.
        data: Optional Glue Data object.
        highlight_bins: Boolean or reactive value to enable bin highlighting.
            - Default: True for BinHighlighter, False for PlotlyHighlighting
        show_bins_with_data_only: Boolean or reactive value to only show bins with data.
            - Default: False for both BinHighlighter and PlotlyHighlighting
        use_selection_layer: Boolean to use the selection layer.
            - Default: True for both BinHighlighter and PlotlyHighlighting
        on_click_callback: Optional callback to be called on click.
        on_hover_callback: Optional callback to be called on hover.
        nbins: Integer or reactive value for the number of bins.
            - Default: 15 for both BinHighlighter and PlotlyHighlighting
        bin_width: Float or reactive value for the bin width.
            - Default: 1.0 for both BinHighlighter and PlotlyHighlighting
        use_python_highlighing: Boolean to use Python-based highlighting (BinHighlighter) or Plotly-based highlighting (PlotlyHighlighting).
            - Default: True for BinHighlighter, False for PlotlyHighlighting

    Explanation:
        - `use_selection_layer`: When set to True, the selection layer is used to handle interactions like clicks and hovers. This is useful for more complex interactions.
        - `show_bins_with_data_only`: When set to True, only bins that contain data will be shown. This helps in focusing on relevant data points.
        - `highlight_bins`: When set to True, bins will be highlighted based on interactions like hover or click. This is useful for visual emphasis on certain data points.
        - `use_python_highlighing`: When set to False, the PlotlyHighlighter is used, which does not emit hover events. Instead, it highlights elements based on mouse movements over the plot.

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
    viewer_container = rv.Html(tag='div', style_=f"width: 100%; height: 100%") # type: ignore

    highlight_bins = solara.use_reactive(highlight_bins)
    nbins = solara.use_reactive(nbins)
    bin_width = solara.use_reactive(bin_width)
    show_bins_with_data_only = solara.use_reactive(show_bins_with_data_only)

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
        viewer.figure_widget.update_layout(height=None, width=None)
        viewer.figure_widget.update_layout(autosize=True, height=300)
        
        vc = solara.get_widget(viewer_container)

        viewer.state.hist_n_bin = nbins.value
        nbins.subscribe(lambda x: setattr(viewer.state, 'hist_n_bin', x))
        
        def on_click(trace, points, state):
            if on_click_callback is not None:
                on_click_callback(points)
            if len(points.xs) == 0:
                print('No points selected')
        
        viewer.selection_layer.on_click(on_click)
        
        # Create BinHighlighter instance
        if use_python_highlighing:
            vc.children = (viewer.figure_widget,) # type: ignore
            
            def on_hover(trace, points, state):
                if on_hover_callback is not None:
                    on_hover_callback(points)
            
            bin_highlighter = BinHighlighter(viewer, 
                                            line_color='rgba(255, 120, 255, 1)',
                                            fill_color='rgba(0,0,0,.5)',
                                            visible_bins=True,
                                            show_bins_with_data_only=True,
                                            on_hover_callback=on_hover,
                                            on_click_callback=on_click,
                                            use_selection_layer=use_selection_layer,
                                            setup_selection_layer=True,
                                            only_show=False,
                                            )

            if highlight_bins.value:
                bin_highlighter.setup_bin_highlight()

            def toggle_bin_highlight(turn_on: bool):
                if bin_highlighter is None:
                    return
                if turn_on:
                    bin_highlighter.turn_on_bin_highlight()
                else:
                    bin_highlighter.turn_off_bin_highlight()
            
            toggle_bin_highlight(highlight_bins.value)
            highlight_bins.subscribe(toggle_bin_highlight)      
            
            def on_nbins_change(value):
                if bin_highlighter is not None:
                    bin_highlighter.redraw()
            nbins.subscribe(on_nbins_change)
            
            def on_bin_width_change(value):
                if bin_highlighter is not None:
                    bin_highlighter.set_visible_bin_width(value)
            bin_width.subscribe(on_bin_width_change)
            
        else:
            bin_shower = BinManager(viewer,
                                    bin_width=bin_width.value,
                                    selection_bin_width=bin_width.value,
                                    visible_bins=True,
                                    show_bins_with_data_only=show_bins_with_data_only.value,
                                    use_selection_layer=use_selection_layer,
                                    on_click=on_click,
            )
            bin_shower.setup_bin_layer()
            # bin_shower.add_callbacks_to_selection_layer()
            def on_nbins_change(value):
                if bin_shower is not None:
                    bin_shower.redraw_bins()
            nbins.subscribe(on_nbins_change)
            
            def on_bin_width_change(value):
                if bin_shower is not None:
                    bin_shower.set_visible_bin_width(value)
            bin_width.subscribe(on_bin_width_change)
            
            # debug = True will show redo button if not bins are found
            options = {
                'fillColor': 'rgba(0, 0, 0)',
                'fillOpacity': 0.5,
                'strokeColor': 'rgba(255, 0, 255, 1)',
                'strokeOpacity': 1,
                'strokeWidth': 1,
                'opacity': 1,
                'debug': False,
                'show': True
            }
            vc.children = (_PlotlyHighlighting(viewer_id=viewer._unique_class, **options), viewer.figure_widget,) # type: ignore

        def cleanup():
                vc.children = () # type: ignore
                viewer.figure_widget.close()

        return cleanup

    solara.use_effect(lambda :_viewer_setup(data), dependencies=[show_bins_with_data_only.value, use_python_highlighing, use_selection_layer])
    
    return viewer_container



