from aeris.content import CaptureStore,Note
from aeris.editor import Editor
class CaptureWindow(Editor):
    def __init__(self,parent,store): super().__init__(parent,store,False)
