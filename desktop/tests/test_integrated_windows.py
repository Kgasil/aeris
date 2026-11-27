"""Lifecycle smoke for every catalog entry with synthetic settings; no native I/O actions."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import gc
import sys
import tkinter as tk
import unittest
from unittest.mock import patch
from aeris.experience import ExperienceHub
from aeris.permissions import CAPABILITIES
from aeris.settings import Settings


class IntegratedWindows(unittest.TestCase):
    def test_all_catalog_entries_open_without_grants_and_release_windows(self):
        with TemporaryDirectory() as directory:
            root=tk.Tk()
            hub=ExperienceHub(root,Settings(Path(directory)/'settings.json'))
            errors=[]
            root.report_callback_exception=lambda *args: errors.append(args[1])
            try:
                root.update()
                names={module.name for module in hub.modules}
                self.assertEqual(len(names),50)
                self.assertEqual(names,set(hub.tool_buttons)|{'Hub','Spotlight','Privacy','Permissions'})
                self.assertTrue(root.winfo_exists())
                self.assertEqual(hub.settings.appearance.theme,'Escuro')
                hub.settings.set_appearance(replace(hub.settings.appearance,floating_enabled=True))
                hub.apply_appearance(); root.update()
                self.assertIsNotNone(hub.spotlight)
                hub.hide_spotlight(); root.update()
                self.assertIsNone(hub.spotlight)
                for name in sorted(names-{'Hub','Spotlight'}):
                    with self.subTest(tool=name):
                        if name=='Privacy': hub.open_privacy()
                        elif name=='Permissions': hub.open_permissions()
                        else:
                            if not hub.enabled(name): hub.toggle_tool(name)
                            if sys.platform != 'win32' and name in {'Autofill','Bookmarks','Vault'}:
                                with patch('aeris.hub.messagebox.showinfo') as info:
                                    hub.open_tool(name)
                                info.assert_called_once()
                                self.assertIsNone(getattr(hub,name.lower()+'_window'))
                                self.assertFalse(any(hub.permissions.allowed(cap) for cap in CAPABILITIES))
                                continue
                            hub.open_tool(name)
                        attr=name.lower()+'_window'
                        obj=getattr(hub,attr)
                        self.assertTrue(hub.alive(obj))
                        root.update()
                        self.assertFalse(any(hub.permissions.allowed(cap) for cap in CAPABILITIES))
                        obj.window.destroy(); root.update()
                        self.assertIsNone(getattr(hub,attr))
                self.assertEqual(errors,[])
            finally:
                root.destroy()
                hub=None; root=None; gc.collect()


if __name__=='__main__': unittest.main()
