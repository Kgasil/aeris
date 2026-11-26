"""Core regression with a real Tk root and synthetic, temporary settings."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from unittest import TestCase, main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings, Appearance
from aeris.permissions import CREATE_BACKUP, RESTORE_BACKUP, BRIDGE_RUN, BRIDGE_SAVE, BRIDGE_COPY
from aeris.backup import BackupService

class CoreRefinement(TestCase):
    def _collect_ui(self):
        import gc
        self.h=None
        self.root=None
        gc.collect()

    def setUp(self):
        self.addCleanup(self._collect_ui)
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk()
        self.addCleanup(self.root.destroy)
        self.h=Hub(self.root, Settings(Path(self.tmp.name)/"settings.json"))
        self.root.update()

    def open(self,name):
        if not self.h.enabled(name):
            self.h.toggle_tool(name)
        self.h.open_tool(name)
        self.root.update()
        return getattr(self.h,name.lower()+"_window")

    def test_hub_preserves_selection_and_keyboard_open(self):
        h=self.h
        index=next(i for i,m in enumerate(h.visible) if m.name=="Health")
        h.listbox.selection_clear(0,"end")
        h.listbox.selection_set(index)
        h.category.set("Core")
        self.assertEqual(h.visible[h.listbox.curselection()[0]].name,"Health")
        h.toggle_tool("Health")
        self.assertEqual(h.open_selected(),"break")
        self.assertTrue(h.alive(h.health_window))
        h.query.set("no matching tool")
        self.assertFalse(h.visible)
        h.open_selected()
        h.clear_filters()
        self.assertEqual((h.query.get(),h.category.get(),len(h.visible)),("", "Todas",50))

    def test_spotlight_keyboard_controls(self):
        h=self.h
        h.settings.set_appearance(Appearance(floating_enabled=True))
        h.apply_appearance()
        self.root.update()
        s=h.spotlight
        self.assertEqual(int(s.button.cget("highlightthickness")),2)
        self.assertTrue(s.button.bind("<Shift-F10>"))
        s.show_panel()
        self.root.update()
        self.assertTrue(s.panel.winfo_exists())
        self.assertTrue(s.panel.bind("<Escape>"))
        self.assertEqual(s.dismiss_and_focus(),"break")
        self.assertIsNone(s.panel)

    def test_health_finish_after_disable(self):
        ui=self.open("Health")
        ui.run()
        ui.window.after_cancel(ui.pending)
        with patch.object(self.h,"enabled",return_value=False):
            ui.finish()
        self.assertIsNone(ui.pending)
        self.assertEqual(str(ui.button.cget("state")),"normal")
        self.assertEqual(ui.report.get(),"Sem amostra.")

    def test_backup_changed_after_inspection_is_rejected(self):
        h=self.h
        for permission in (CREATE_BACKUP,RESTORE_BACKUP):
            h.permissions.set(permission,True)
        service=BackupService(h.settings,h.permissions)
        path=Path(self.tmp.name)/"first.aerisbackup"
        second=Path(self.tmp.name)/"second.aerisbackup"
        service.create(path)
        names,digest=service.inspect_with_digest(path)
        self.assertEqual(names,("Aparência",))
        h.settings.set_appearance(Appearance(theme="Escuro"))
        service.create(second)
        path.write_bytes(second.read_bytes())
        h.settings.set_appearance(Appearance(theme="Claro"))
        with self.assertRaisesRegex(ValueError,"alterado"):
            service.restore(path,"Aparência",expected_digest=digest)
        self.assertEqual(h.settings.appearance.theme,"Claro")
        _,new_digest=service.inspect_with_digest(path)
        service.restore(path,"Aparência",expected_digest=new_digest)
        self.assertEqual(h.settings.appearance.theme,"Escuro")

    def test_bridge_rejects_unprocessed_input_change(self):
        h=self.h
        for name in ("Capture","Text","Bridge"):
            if not h.enabled(name): h.toggle_tool(name)
        ui=self.open("Bridge")
        for permission in (BRIDGE_RUN,BRIDGE_SAVE,BRIDGE_COPY):
            h.permissions.set(permission,True)
        ui.route.set("Text → Capture")
        ui.input.insert("1.0","Texto fictício")
        self.root.update()
        ui.run()
        self.assertIsNotNone(ui.preview)
        ui.input.insert("end"," alterado")
        # No Tk update; a queued Modified event must not authorize the old preview.
        ui.save()
        self.assertIsNone(ui.preview)
        self.assertIsNone(h.capture_store)

    def test_bridge_rejects_changed_title_during_confirmation(self):
        h=self.h
        for name in ("Capture","Text","Bridge"):
            if not h.enabled(name): h.toggle_tool(name)
        ui=self.open("Bridge")
        for permission in (BRIDGE_RUN,BRIDGE_SAVE): h.permissions.set(permission,True)
        ui.route.set("Text → Capture")
        ui.input.insert("1.0","Texto fictício")
        self.root.update(); ui.run()
        def changed(*args,**kwargs):
            ui.title.set("Outro título")
            return True
        with patch("aeris.bridge_ui.messagebox.askyesno",side_effect=changed):
            ui.save()
        self.assertIsNone(h.capture_store)
        self.assertIn("alterada",ui.status.get())

if __name__=="__main__": main(verbosity=2)
