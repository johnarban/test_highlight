import solara
from .BinManager import BinManager
from ipyvuetify import VuetifyTemplate
import os
from traitlets import Unicode, Bool

class _PlotlyHighlighting(VuetifyTemplate):
    template_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "PlotlyHighlighting.vue"))
    viewer_id = Unicode().tag(sync=True)
    show = Bool(False).tag(sync=True)
    highlight = Bool(True).tag(sync=True)
    
    def __init__(self, viewer_id = '', show = False, highlight = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewer_id = viewer_id
        self.show = show
        self.highlight = highlight
        pass


@solara.component
def PlotlyHighlighting(viewer_id='', show=False, highlight=True):
    return _PlotlyHighlighting(viewer_id=viewer_id, show=show, highlight=highlight)

    
    
# @solara.component_vue('PlotlyHighlighting.vue')
# def PlotlyHighlighting():
#     pass

