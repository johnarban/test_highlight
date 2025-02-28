import solara
import reacton.ipyvuetify as rv

from hubbleds.viewers.hubble_dotplot import HubbleDotPlotView, HubbleDotPlotViewer
from glue.core import Data
import numpy as np
from typing import Callable, Optional, List, cast
from .bin_highligher import BinHighlighter
from .BinManager import BinManager
from .PlotlyHighlighting import _PlotlyHighlighting

@solara.component
def TestViewer(gjapp, 
               data: Optional[Data] = None, 
               highlight_bins: solara.Reactive[bool] | bool = False,    
               only_show_bins: solara.Reactive[bool] | bool = False, 
               use_selection_layer: solara.Reactive[bool] | bool = False,
               on_click_callback = None, 
               on_hover_callback = None,
               nbins: solara.Reactive[int] | int = 5,
               bin_width: solara.Reactive[float] | float = 1,
               use_python_highlighing: bool = True
               ):
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
    viewer_container = rv.Html(tag='div', style_=f"width: 100%; height: 100%") # type: ignore
    use_selection_layer = solara.use_reactive(use_selection_layer)
    highlight_bins = solara.use_reactive(highlight_bins)
    bin_highlighter: solara.Reactive[BinHighlighter | None] = solara.use_reactive(None)
    nbins = solara.use_reactive(nbins)
    bin_width = solara.use_reactive(bin_width)
    only_show_bins = solara.use_reactive(only_show_bins)
    viewer_class = solara.use_reactive('')

    
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
        viewer_class.set(viewer._unique_class)
        
        viewer.state.hist_n_bin = nbins.value
        nbins.subscribe(lambda x: setattr(viewer.state, 'hist_n_bin', x))
        
        def on_click(trace, points, state):
            if on_click_callback is not None:
                on_click_callback(points)
        
        
        viewer.selection_layer.on_click(on_click)
    
        # Create BinHighlighter instance
        if use_python_highlighing:
            bin_highlighter.set(BinHighlighter(viewer, 
                                            on_hover_callback=on_hover_callback,
                                            bin_width=bin_width.value, 
                                            use_selection_layer=use_selection_layer.value,
                                            selection_bin_width=bin_width.value,
                                            show_bins_with_data_only=False,
                                            visible_bins=True,
                                            setup_selection_layer=True,
                                            only_show=only_show_bins.value,
                                            ))

            def toggle_bin_highlight(turn_on: bool):
                if bin_highlighter.value is None:
                    return
                if turn_on:
                    bin_highlighter.value.turn_on_bin_highlight()
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
                    bin_highlighter.value.set_visible_bin_width(value)
            bin_width.subscribe(on_bin_width_change)
            
        else:
        
            bin_shower = BinManager(viewer,
                                    bin_width=bin_width.value,
                                    selection_bin_width=bin_width.value,
                                    visible_bins=True,
                                    show_bins_with_data_only=False,
                                    use_selection_layer=False
            )
            bin_shower.setup_bin_layer()
            def on_nbins_change(value):
                if bin_shower is not None:
                    bin_shower.redraw_bins()
            nbins.subscribe(on_nbins_change)
            
            def on_bin_width_change(value):
                if bin_shower is not None:
                    bin_shower.set_visible_bin_width(value)
            bin_width.subscribe(on_bin_width_change)
        
        def cleanup():
                vc.children = () # type: ignore
                viewer.figure_widget.close()

        return cleanup


    

    
    solara.use_effect(lambda :_viewer_setup(data), dependencies=[only_show_bins.value, use_python_highlighing])
    
    def add_highlighting():
        print('adding highlighting', viewer_class.value)
        pl = _PlotlyHighlighting(viewer_id=viewer_class.value)
        vc = solara.get_widget(viewer_container)
        vc.children = (pl, ) + tuple(vc.children) # type: ignore
    
    # solara.use_effect(add_highlighting, dependencies=[viewer_class.value])
    viewer_class.subscribe(lambda x: add_highlighting())
    
    return viewer_container



