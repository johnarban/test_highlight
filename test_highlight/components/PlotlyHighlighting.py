# type: ignore
import solara
from .BinManager import BinManager
from ipyvuetify import VuetifyTemplate
import os
from traitlets import Unicode, Bool, Float

class _PlotlyHighlighting(VuetifyTemplate):
    template_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "PlotlyHighlighting.vue"))
    viewer_id = Unicode().tag(sync=True)
    show = Bool(False).tag(sync=True)
    highlight = Bool(True).tag(sync=True)
    debug = Bool(False).tag(sync=True)
    fillColor = Unicode('rgba(0, 0, 0)').tag(sync=True)
    fillOpacity = Float(0.5).tag(sync=True)
    strokeColor = Unicode('rgba(255, 120, 255, 1)').tag(sync=True)
    strokeOpacity = Float(1).tag(sync=True)
    strokeWidth = Float(1).tag(sync=True)
    opacity = Float(1).tag(sync=True)
    
    def __init__(self, viewer_id = '', show = False, highlight = True, debug = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewer_id = viewer_id
        self.show = show
        self.highlight = highlight
        self.debug = debug
        pass


@solara.component
def PlotlyHighlighting(viewer_id='', show=False, highlight=True, debug = False):
    return _PlotlyHighlighting(viewer_id=viewer_id, show=show, highlight=highlight, debug=debug)

    
    
# @solara.component_vue('PlotlyHighlighting.vue')
# def PlotlyHighlighting():
#     pass

