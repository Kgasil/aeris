"""Entry-point helpers shared by source and frozen Windows builds."""
import sys
from contextlib import contextmanager

APP_MUTEX = r'Local\KGVision.Aeris.Desktop'


def frozen():
    return bool(getattr(sys, 'frozen', False))


def translation_worker_available():
    # Optional Argos uses a separate interpreter. A frozen executable is not one.
    return not frozen()


@contextmanager
def application_lock():
    """Prevent overlapping installed instances; never silently ignore mutex errors."""
    if sys.platform != 'win32' or not frozen():
        yield True
        return
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateMutexW
    create.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    ctypes.set_last_error(0)
    handle = create(None, False, APP_MUTEX)
    error = ctypes.get_last_error()
    if not handle:
        raise ctypes.WinError(error)
    try:
        yield error != 183  # ERROR_ALREADY_EXISTS
    finally:
        close(handle)


def self_test(full=False):
    """Create a hidden Hub using temporary preferences; never open personal files."""
    import tempfile
    from pathlib import Path
    import tkinter as tk
    from aeris.experience import ExperienceHub
    from aeris.registry import load_catalog
    from aeris.settings import Settings
    modules = load_catalog()
    if len(modules) != 50 or len({m.name for m in modules}) != 50:
        raise RuntimeError('Invalid packaged catalog')
    with tempfile.TemporaryDirectory(prefix='aeris-check-') as directory:
        root = tk.Tk()
        try:
            root.withdraw()
            errors = []
            root.report_callback_exception = lambda kind, value, tb: errors.append(value)
            hub = ExperienceHub(root, Settings(Path(directory) / 'settings.json'))
            root.update_idletasks()
            root.update()
            if len(hub.modules) != 50:
                raise RuntimeError('Incomplete Hub')
            if not hub.conversation.idle():
                raise RuntimeError('Unexpected activity on startup')
            for view in ('screen','notes','meeting','catalog','chat'):
                hub.navigate(view)
                root.update()
                if hub.view != view: raise RuntimeError('Navigation failed: '+view)
            hub.conversation.toggle_ai_settings()
            root.update()
            if not hub.conversation.ai_open or not hub.conversation.ai_settings.winfo_manager():
                raise RuntimeError('Readiness panel did not open')
            hub.conversation.toggle_ai_settings()
            root.update()
            if hub.conversation.ai_open or hub.conversation.ai_settings.winfo_manager():
                raise RuntimeError('Readiness panel did not close')
            # Synthetic visual draft: no screen, microphone or AI access.
            from aeris.visual_question import VisualQuestion
            conversation=hub.conversation
            conversation.screen_question=VisualQuestion(b'fake-image','local')
            conversation.input.insert('1.0','Pergunta fictícia')
            root.update()
            conversation.detach_question()
            conversation.refresh()
            if not conversation.visual_invalid or conversation.screen_question is not None:
                raise RuntimeError('Visual draft invalidation failed')
            conversation.send()
            if conversation.busy or conversation.input.get('1.0','end-1c')!='Pergunta fictícia':
                raise RuntimeError('Invalid visual draft was sent or lost')
            conversation.release_question()
            if conversation.visual_invalid:
                raise RuntimeError('Explicit text-only release failed')
            conversation.input.delete('1.0','end')
            root.update()
            if full:
                # Opening windows only: no clipboard, external files, audio, AI or user records.
                from dataclasses import replace
                from aeris.settings import FLAGS
                protected = {'Vault', 'Bookmarks', 'Autofill'}
                if len(hub.tool_buttons) != 46 or len(FLAGS) != 46:
                    raise RuntimeError('Incomplete optional modules')
                for name in hub.tool_buttons:
                    if sys.platform != 'win32' and name in protected:
                        continue
                    hub.settings.set_module(name, True)
                    hub.open_tool(name)
                    attr = name.lower() + '_window'
                    root.update()
                    if not hub.alive(getattr(hub, attr)):
                        raise RuntimeError('Tool did not open: ' + name)
                    hub.close_window(attr)
                    root.update()
                hub.open_privacy(); root.update()
                if not hub.alive(hub.privacy_window): raise RuntimeError('Missing Privacy')
                hub.close_window('privacy_window')
                hub.open_permissions(); root.update()
                if not hub.alive(hub.permissions_window): raise RuntimeError('Missing Permissions')
                hub.close_window('permissions_window')
                hub.settings.set_appearance(replace(hub.settings.appearance, floating_enabled=True))
                hub.refresh_spotlight(); root.update()
                if hub.spotlight is None: raise RuntimeError('Missing Spotlight')
                hub.spotlight.destroy(); hub.spotlight = None
                hub.reset_reminders()
            if errors:
                raise RuntimeError('Tk callback failed') from errors[0]
        finally:
            root.destroy()
    return 0
