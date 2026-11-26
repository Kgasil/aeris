"""Real Tk file-tool regressions using temporary, synthetic files only."""
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import tkinter as tk
from unittest import TestCase, main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import DOCUMENTS_READ,ORGANIZER_SCAN,DROP_ADD,DROP_COPY,COMPARE_READ,LENS_READ
from aeris.lens import LensResult,Cancelled
from aeris.drop import inspect_paths

class FilesRefinement(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk(); self.addCleanup(self.root.destroy)
        self.base=Path(self.tmp.name)
        self.h=Hub(self.root,Settings(self.base/'settings.json')); self.root.update()
    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+'_window')
    def file(self,name,data):
        p=self.base/name; p.write_bytes(data); return p
    def choose(self,ui,module,path,permission,directory=False):
        self.h.permissions.set(permission,True)
        method='askdirectory' if directory else 'askopenfilename'
        with patch(f'aeris.{module}_ui.filedialog.{method}',return_value=str(path)): ui.choose()
    def wait(self,ui):
        deadline=time.monotonic()+5
        while ui.job and time.monotonic()<deadline: self.root.update(); time.sleep(.02)
        self.assertIsNone(ui.job)
    def test_documents_changed_selection_not_read(self):
        ui=self.open('Documents')
        a=self.file('a.txt',b'Original'); b=self.file('b.txt',b'Other')
        self.choose(ui,'documents',a,DOCUMENTS_READ)
        def changed(*args,**kwargs):
            self.choose(ui,'documents',b,DOCUMENTS_READ); return True
        with patch('aeris.documents_ui.messagebox.askyesno',side_effect=changed),patch('aeris.documents_ui.extract_file') as read:
            ui.run(); read.assert_not_called()
        self.assertIsNone(ui.job); self.assertEqual(ui.path,str(b))
    def test_documents_find_next_wrap_and_clear(self):
        ui=self.open('Documents'); a=self.file('a.txt',b'alpha\nbeta\nAlpha\n')
        self.choose(ui,'documents',a,DOCUMENTS_READ)
        with patch('aeris.documents_ui.messagebox.askyesno',return_value=True): ui.run()
        self.wait(ui); ui.query.set('alpha')
        ui.find_next(); first=ui.report.tag_ranges('found')
        ui.find_next(); second=ui.report.tag_ranges('found')
        self.assertTrue(first); self.assertNotEqual(first,second)
        ui.find_next(); self.assertEqual(ui.report.tag_ranges('found'),first)
        self.h.permissions.set(DOCUMENTS_READ,False)
        self.assertFalse(ui.report.tag_ranges('found')); self.assertEqual(ui.query.get(),'')
        self.assertEqual(a.read_bytes(),b'alpha\nbeta\nAlpha\n')
    def test_organizer_sort_and_revocation(self):
        ui=self.open('Organizer'); p=self.base/'samples'; p.mkdir()
        (p/'a.txt').write_bytes(b'1'); (p/'z.csv').write_bytes(b'12345')
        self.choose(ui,'organizer',p,ORGANIZER_SCAN,True)
        with patch('aeris.organizer_ui.messagebox.askyesno',return_value=True): ui.run()
        self.wait(ui); ui.order.set('Maior tamanho'); ui.render_inventory()
        result=ui.report.get('1.0','end')
        self.assertIn('Tamanho total listado: 6 bytes',result)
        self.assertLess(result.index('z.csv'),result.index('a.txt'))
        self.h.permissions.set(ORGANIZER_SCAN,False); self.assertIsNone(ui.inventory)
        ui.render_inventory(); self.assertNotIn('z.csv',ui.report.get('1.0','end'))
        self.assertEqual((p/'z.csv').read_bytes(),b'12345')
    def test_drop_selection_summary_and_changed_references(self):
        ui=self.open('Drop')
        for perm in (DROP_ADD,DROP_COPY): self.h.permissions.set(perm,True)
        a=self.file('a.txt',b'abc'); b=self.file('b.txt',b'12345')
        ui.store.add(inspect_paths((str(a),str(b)))); ui.refresh()
        ui.listbox.selection_set(0); ui.controls(); ui.refresh()
        self.assertEqual(ui.selected(),(str(a),))
        self.assertIn('1 selecionadas | 3 bytes',ui.summary.get())
        ui.select_all(); self.assertIn('2 selecionadas | 8 bytes',ui.summary.get())
        def changed(*args,**kwargs):
            ui.clear(); ui.store.add(inspect_paths((str(a),str(b)))); ui.refresh(); ui.select_all()
            return True
        with patch('aeris.drop_ui.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()
        ui.unselect_all(); self.assertFalse(ui.selected())
        self.assertEqual(a.read_bytes(),b'abc')
    def test_compare_filter_and_stale_result(self):
        ui=self.open('Compare')
        ui.inputs[0].insert('1.0','same\nold'); ui.inputs[1].insert('1.0','same\nnew')
        self.root.update(); ui.run(); self.wait(ui)
        self.assertIn('same',ui.report.get('1.0','end'))
        ui.changes_only.set(True); ui.render_comparison()
        result=ui.report.get('1.0','end')
        self.assertNotIn('same',result); self.assertIn('old',result); self.assertIn('new',result)
        self.assertIn('Mantidas: 1',ui.status.get())
        ui.inputs[0].insert('end','!')
        ui.render_comparison(); self.assertIsNone(ui.comparison)
        self.assertFalse(ui.report.get('1.0','end-1c'))
    def test_lens_language_change_before_confirmation(self):
        ui=self.open('Lens'); p=self.file('fake.png',b'synthetic')
        self.choose(ui,'lens',p,LENS_READ)
        def changed(*args,**kwargs): ui.language.set('English'); return True
        with patch('aeris.lens_ui.messagebox.askyesno',side_effect=changed),patch('aeris.lens_ui.recognize') as ocr:
            ui.run(); ocr.assert_not_called()
        self.assertIsNone(ui.job)
    def test_lens_language_change_cancels_and_relabels_result(self):
        ui=self.open('Lens'); p=self.file('fake.png',b'synthetic')
        self.choose(ui,'lens',p,LENS_READ)
        def slow(*args,cancelled):
            deadline=time.monotonic()+3
            while not cancelled() and time.monotonic()<deadline: time.sleep(.01)
            if cancelled(): raise Cancelled()
            return LensResult('obsolete',False,'PNG',20,20)
        with patch('aeris.lens_ui.recognize',side_effect=slow),patch('aeris.lens_ui.messagebox.askyesno',return_value=True):
            ui.run(); self.assertIsNotNone(ui.job); ui.language.set('English'); self.wait(ui)
        self.assertIn('Idioma alterado',ui.report.get('1.0','end'))
        self.assertNotIn('obsolete',ui.report.get('1.0','end'))
        with patch('aeris.lens_ui.recognize',return_value=LensResult('new',False,'PNG',20,20)),patch('aeris.lens_ui.messagebox.askyesno',return_value=True):
            ui.run(); self.wait(ui)
        self.assertIn('Idioma: English',ui.report.get('1.0','end')); self.assertEqual(p.read_bytes(),b'synthetic')

if __name__=='__main__': main(verbosity=2)
