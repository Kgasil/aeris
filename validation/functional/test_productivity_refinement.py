"""Regression of refined Productivity behavior in an isolated synthetic Tk session."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import tkinter as tk
from unittest import TestCase,main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.focus import MODES
from aeris.reminder import ReminderStore
from aeris.permissions import ROUTINE_RUN,ROUTINE_COPY,BRIDGE_RUN

class ProductivityRefinement(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk()
        self.addCleanup(self.root.destroy)
        self.h=Hub(self.root,Settings(Path(self.tmp.name)/"settings.json"))
        self.root.update()

    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+"_window")

    def test_focus_presets_do_not_interrupt_active_timer(self):
        ui=self.open("Focus"); ui.preset(MODES[0],50)
        self.assertEqual(ui.display.get(),"50:00")
        ui.start()
        self.assertEqual(str(ui.preset_buttons[0].cget("state")),"disabled")
        ui.preset(MODES[1],5)
        self.assertEqual(ui.model.minutes,50)
        ui.pause(); ui.preset(MODES[1],5)
        self.assertEqual(ui.model.mode,MODES[0])
        ui.reset(); ui.preset(MODES[1],5)
        self.assertEqual(ui.display.get(),"05:00")

    def test_workspace_changed_during_delete_is_not_deleted(self):
        ui=self.open("Workspace")
        ui.store.save("Estudos",["Focus"],[])
        ui.refresh("Estudos")
        def changed(*args,**kwargs):
            ui.store.save("Estudos",["Checklist"],[])
            return True
        with patch("aeris.workspace_ui.messagebox.askyesno",side_effect=changed): ui.delete()
        self.assertEqual(ui.store.get("Estudos").tools,("Checklist",))
        self.assertIn("alterada",ui.status.get())
        ui.store.delete("Estudos")
        ui.refresh_actions(); ui.activate()
        self.assertIsNone(ui.store.active)

    def test_checklist_priority_filter_and_selection(self):
        ui=self.open("Checklist")
        ui.store.create("Teste"); a=ui.store.add("Teste","A","Alta"); b=ui.store.add("Teste","B","Baixa")
        ui.refresh_lists("Teste"); ui.tree.selection_set(str(a.id))
        ui.priority_filter.set("Alta"); ui.render()
        self.assertEqual(ui.tree.get_children(),(str(a.id),))
        self.assertEqual(ui.tree.selection(),(str(a.id),))
        ui.toggle()
        self.assertTrue(ui.store.tasks("Teste")[0].done)
        ui.filter.set("Pendentes"); ui.render()
        self.assertFalse(ui.tree.get_children())
        self.assertEqual(ui.stats.get(),"1 de 2 concluídas")
        ui.toggle_row(SimpleNamespace(x=1,y=-10))
        self.assertFalse(ui.store.tasks("Teste")[1].done)

    def test_reminder_cannot_reschedule_or_cancel_after_deadline(self):
        now=[1000.0]; store=ReminderStore(lambda:now[0])
        a=store.add("Teste",1,True)
        now[0]=1060.0
        with self.assertRaises(ValueError): store.edit(a.id,"Outro",5)
        with self.assertRaises(ValueError): store.cancel(a.id)
        self.assertEqual(store.collect_due()[0].id,a.id)
        self.assertEqual(store.collect_due(),())

    def routine(self):
        for name in ("Bridge","Expand","Text","Capture"):
            if not self.h.enabled(name): self.h.toggle_tool(name)
        ui=self.open("Routine")
        ui.add(); ui.step.set("Text → Capture"); ui.add()
        ui.input.insert("1.0","  ;att  "); self.root.update()
        for cap in (ROUTINE_RUN,BRIDGE_RUN,ROUTINE_COPY): self.h.permissions.set(cap,True)
        ui.run()
        self.assertIsNotNone(ui.preview)
        return ui

    def test_routine_stale_input_before_event_dispatch(self):
        ui=self.routine(); ui.input.insert("end","!")
        with patch.object(self.root,"clipboard_clear") as clear:
            ui.copy(); clear.assert_not_called()
        self.assertIsNone(ui.preview)

    def test_routine_replaced_preview_during_confirmation(self):
        ui=self.routine()
        def changed(*args,**kwargs):
            ui.run()
            return True
        with patch("aeris.routine_ui.messagebox.askyesno",side_effect=changed), patch.object(self.root,"clipboard_clear") as clear:
            ui.copy(); clear.assert_not_called()
        self.assertIn("alterada",ui.status.get())

if __name__=="__main__": main(verbosity=2)
