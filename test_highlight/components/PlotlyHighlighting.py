import solara
from .BinManager import BinManager
from ipyvuetify import VuetifyTemplate
import os
from traitlets import Unicode

class _PlotlyHighlighting(VuetifyTemplate):
    template_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "PlotlyHighlighting.vue"))
    viewer_id = Unicode().tag(sync=True)
    
    def __init__(self, viewer_id = '', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewer_id = viewer_id
        pass


@solara.component
def PlotlyHighlighting():
    _PlotlyHighlighting.element()
    
    
# @solara.component_vue('PlotlyHighlighting.vue')
# def PlotlyHighlighting():
#     pass

