"""Release closed UI references; persistent session stores are deliberately separate."""
import tkinter as tk
import weakref


def track_window(owner, attr):
    """Forget only the exact instance destroyed, never a replacement window."""
    obj = getattr(owner, attr)
    window = obj.window
    ref = weakref.ref(owner)
    obj_ref = weakref.ref(obj)

    def destroyed(event):
        if event.widget is not window:
            return
        parent = ref()
        if parent is not None and getattr(parent, attr, None) is obj_ref():
            setattr(parent, attr, None)

    window.bind('<Destroy>', destroyed, add='+')


def trace_window(window, variable, callback):
    """Remove a static UI variable's Tcl callback on destruction."""
    token = variable.trace_add('write', callback)

    def destroyed(event):
        if event.widget is window:
            try:
                variable.trace_remove('write', token)
            except tk.TclError:
                pass  # Interpreter may already be shutting down.

    window.bind('<Destroy>', destroyed, add='+')
    return token
