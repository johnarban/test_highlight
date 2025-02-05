import solara
from solara.alias import rv

from ..components import DotplotViewer, TestViewer, PlotlyHighlighting

from glue_jupyter import JupyterApplication
from glue.core import Data
import numpy as np
import asyncio

from cosmicds.utils import _debounce

from hubbleds.remote import LOCAL_API
from hubbleds.data_management import EXAMPLE_GALAXY_SEED_DATA, DB_VELOCITY_FIELD
from hubbleds.state import LOCAL_STATE
from hubbleds.example_measurement_helpers import link_seed_data


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
    
    show_dotplot = solara.use_reactive(True)
    
    nbins = solara.use_reactive(25)
    bin_width = solara.use_reactive(1.0)
    
    use_selection_layer = solara.use_reactive(True)
    
    def _glue_setup():
        glue_app = JupyterApplication()
        x = list(np.random.normal(0,3, 200)) + list(np.random.normal(20,1, 200))
        data = Data(label='Dotplot Data', x = x)
        glue_app.data_collection.append(data)
        
        if EXAMPLE_GALAXY_SEED_DATA not in glue_app.data_collection:
            example_seed_data = LOCAL_API.get_example_seed_measurement(LOCAL_STATE, which='both')
            
            data = Data(
                label=EXAMPLE_GALAXY_SEED_DATA,
                **{
                    k: np.asarray([r[k] for r in example_seed_data])
                    for k in example_seed_data[0].keys()
                }
            )
            glue_app.data_collection.append(data)
            # create 'first measurement' and 'second measurement' datasets
            # create_measurement_subsets(gjapp, data)
            first = Data(label = EXAMPLE_GALAXY_SEED_DATA + '_first', 
                         **{k: np.asarray([r[k] for r in example_seed_data if r['measurement_number'] == 'first'])
                            for k in example_seed_data[0].keys()}
                            )
            first.style.color = '#f6fd31'
            glue_app.data_collection.append(first)
            second = Data(label = EXAMPLE_GALAXY_SEED_DATA + '_second', 
                         **{k: np.asarray([r[k] for r in example_seed_data if r['measurement_number'] == 'second'])
                            for k in example_seed_data[0].keys()}
                            )
            second.style.color = '#d4a4dd'
            glue_app.data_collection.append(second)
            
            link_seed_data(glue_app)
        return glue_app
    
    app = solara.use_memo(_glue_setup)
    
    def click_callback(*args, **kwargs):
        print('clicked!')
        points = args[0]
        if len(points.xs) > 0:
            print(points.xs)
            line_marker_at.value = points.xs[0]
        num_clicks.value += 1
        # line_marker_at.value = args[1].xs[0]
        
    def hover_callback(*args, **kwargs):
        print('hovered!')
        hover_count.value += 1
        # for .5seconds set is_hovering to True
        is_hovering.value = True
        try:
            hover_location.value = args[1].xs[0]
        except:
            hover_location.value = args[0].xs[0]
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
            solara.Text(f'Click is at: {line_marker_at.value}')
            solara.Text(f'Hover is at: {hover_location.value}')
            solara.Switch(
                label = "Show dotplot",
                value = show_dotplot
            )
            # create a circular div that is green or red  if clicked or not
            with rv.Html(tag='span',style_="display: flex; gap:15px; align-items: center;"):
                solara.Text('Hovering: ')
                rv.Html(tag='div', style_=f"width: 15px; height: 15px; border-radius: 50%; background-color: {'green' if is_hovering.value else 'red'}")
            with solara.Card(style='width: 500px'):
                solara.SliderInt(label='Number of Bins', value=nbins, min=1, max=100)
                solara.SliderFloat(label='Bin Width', value=bin_width, min=0.1, max=1)
            # PlotlyHighlighting()

    with solara.Card(margin=10):
        if show_dotplot.value:
            DotplotViewer(
                app, 
                # data=app.data_collection[EXAMPLE_GALAXY_SEED_DATA], 
                # component_id=DB_VELOCITY_FIELD,
                data = app.data_collection[0],
                component_id='x',
                title = 'Dotplot Viewer',
                on_click_callback = hover_callback,
                vertical_line_visible=vertical_line_visible,
                unit = '#',
                x_label = 'Value',
                y_label = 'Count',
                highlight_bins=highlight_bins,
                nbin=nbins.value,
                use_js = False
                )       
        else:
            TestViewer(app, 
                       data=app.data_collection[0],
                        use_selection_layer=use_selection_layer,
                       on_click_callback=click_callback,
                       on_hover_callback=hover_callback,
                       highlight_bins=highlight_bins,
                       nbins=nbins,
                         bin_width=bin_width,
                       )
        
