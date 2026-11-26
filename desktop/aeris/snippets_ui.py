from aeris.editor import Editor
class SnippetsWindow(Editor):
    def __init__(self,parent,store,permissions=None): super().__init__(parent,store,True,permissions)
