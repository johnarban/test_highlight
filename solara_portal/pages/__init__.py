import solara
from solara.alias import rv

from ..components import DotplotViewer, TestViewer

from glue_jupyter import JupyterApplication
from glue.core import Data
import numpy as np
import asyncio

from cosmicds.utils import _debounce

@solara.component
def Page():
    
    solara.Title('Dotplot Testbed')
    
    vertical_line_visible = solara.use_reactive(False)
    line_marker_at = solara.use_reactive(0)
    hover_location = solara.use_reactive(0)
    highlight_bins = solara.use_reactive(True)
    
    num_clicks = solara.use_reactive(0)
    hover_count = solara.use_reactive(0)
    is_hovering = solara.use_reactive(False)
    
    use_selection_layer = solara.use_reactive(False)
    
    def _glue_setup():
        glue_app = JupyterApplication()
        x = list(np.random.normal(0,3, 200)) + list(np.random.normal(20,1, 200))
        data = Data(label='Dotplot Data', x = x)
        glue_app.data_collection.append(data)
        return glue_app
    
    app = solara.use_memo(_glue_setup)
    
    def dotplot_click_callback(*args, **kwargs):
        print('Dotplot clicked!')
        points = args[1]
        if len(points.xs) > 0:
            print(points.xs)
            line_marker_at.value = points.xs[0]
        num_clicks.value += 1
        # line_marker_at.value = args[1].xs[0]
        
    def dotplot_hover_callback(*args, **kwargs):
        print('Dotplot hovered!')
        hover_count.value += 1
        # for .5seconds set is_hovering to True
        is_hovering.value = True
        hover_location.value = args[1].xs[0]
        # after .5 seconds set is_hovering to False
        async def _set_hovering():
            await asyncio.sleep(1)
            is_hovering.value = False
        asyncio.create_task(_set_hovering())
        
    
    with solara.Column(margin=10):
        with solara.Column():
            solara.Switch(
                label = 'Vertical Line Visible',
                value = vertical_line_visible
                )
            solara.Switch(
                label = 'Use Selection Layer',
                value = use_selection_layer
                )
            solara.Switch(
                label = 'Highlight Bins',
                value = highlight_bins
                )
            solara.Text(f'Number of Clicks: {num_clicks.value}')
            solara.Text(f'Number of Hovers: {hover_count.value}')
            solara.Text(f'Line Marker At: {line_marker_at.value}')
            solara.Text(f'Hover is at: {hover_location.value}')
            # create a circular div that is green or red  if clicked or not
            with rv.Html(tag='span',style_="display: flex; gap:15px; align-items: center;"):
                solara.Text('Hovering: ')
                rv.Html(tag='div', style_=f"width: 15px; height: 15px; border-radius: 50%; background-color: {'green' if is_hovering.value else 'red'}")


    with solara.Card(title='Dotplot Viewer', margin=10):
        # DotplotViewer(
        #     app, 
        #     data=app.data_collection[0], 
        #     component_id='x',
        #     title = 'Dotplot Viewer',
        #     on_click_callback = dotplot_click_callback,
        #     vertical_line_visible=vertical_line_visible,
        #     unit = '#',
        #     x_label = 'Value',
        #     y_label = 'Count',
            
        #     )
        TestViewer(app, 
                   data=app.data_collection[0],
                    use_selection_layer=use_selection_layer,
                   on_click_callback=dotplot_click_callback,
                   on_hover_callback=dotplot_hover_callback,
                   highlight_bins=highlight_bins,
                   )
        
