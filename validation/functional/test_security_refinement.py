"""Real Tk security regressions with synthetic data, temporary files and no network."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import time
import tkinter as tk
from unittest import TestCase,main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import SEARCH_CAPTURE,SEARCH_SNIPPETS,VERIFY_READ,METADATA_READ
from aeris.verify import Cancelled
from aeris.link import inspect_url
from tests.test_metadata import png_sample

class SecurityRefinement(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk(); self.addCleanup(self.root.destroy)
        self.base=Path(self.tmp.name)
        self.h=Hub(self.root,Settings(self.base/'settings.json')); self.root.update()
    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+'_window')
    def choose(self,ui,module,path,permission):
        self.h.permissions.set(permission,True)
        with patch(f'aeris.{module}_ui.filedialog.askopenfilename',return_value=str(path)): ui.choose()
    def wait(self,ui):
        deadline=time.monotonic()+5
        while ui.job and time.monotonic()<deadline: self.root.update(); time.sleep(.02)
        self.assertIsNone(ui.job)
    def test_permission_revocation_invalidates_pending_confirmation_even_when_empty(self):
        self.h.open_permissions(); ui=self.h.permissions_window
        before=self.h.permissions.revision
        def revoke(*args,**kwargs): self.h.permissions.revoke_all(); return True
        with patch('aeris.permissions_ui.messagebox.askyesno',side_effect=revoke): ui.toggle(SEARCH_CAPTURE)
        self.assertGreater(self.h.permissions.revision,before)
        self.assertFalse(self.h.permissions.allowed(SEARCH_CAPTURE))
        self.assertIn('alteradas',ui.status.get())
        with patch('aeris.permissions_ui.messagebox.askyesno',return_value=True): ui.toggle(SEARCH_CAPTURE)
        self.assertTrue(self.h.permissions.allowed(SEARCH_CAPTURE))
        self.assertTrue(ui.summary.get().startswith('1/'))
        ui.toggle(SEARCH_CAPTURE)
        self.assertFalse(self.h.permissions.allowed(SEARCH_CAPTURE))
    def test_privacy_filter_and_mask_counts(self):
        self.h.open_privacy(); ui=self.h.privacy_window
        self.h.permissions.set(SEARCH_CAPTURE,True)
        self.h.permissions.set(SEARCH_SNIPPETS,True)
        ui.granted_only.set(True); ui.refresh()
        self.assertEqual(len(ui.grants.get(0,'end')),2)
        ui.original.insert('1.0','demo@example.org e 000.000.000-00')
        ui.mask()
        self.assertIn('2 padrões mascarados',ui.mask_status.get())
        self.assertIn('E-mail: 1',ui.mask_status.get())
        self.assertIn('CPF formatado: 1',ui.mask_status.get())
        self.assertNotIn('demo@example.org',ui.preview.get('1.0','end'))
        ui.revoke(); self.assertEqual(ui.grants.size(),0)
        ui.reset_mask(); self.assertFalse(ui.preview.get('1.0','end-1c'))
    def test_link_fragment_and_bad_escape_never_echo_values_or_use_network(self):
        ui=self.open('Link'); ui.url.set('https://example.org/a%ZZ#token=FAKESECRET')
        with patch('socket.getaddrinfo',side_effect=AssertionError('network')),patch('socket.socket',side_effect=AssertionError('network')):
            ui.analyze()
        report=ui.report.get('1.0','end')
        self.assertIn('Fragmento presente',report)
        self.assertIn('Sequência percentual',report)
        self.assertIn('não é pontuação de risco',report)
        self.assertNotIn('FAKESECRET',report)
        self.assertEqual(inspect_url('https://example.org/').indicators,())
        ui.clear(); self.assertNotIn('example.org',ui.report.get('1.0','end'))
    def test_verify_changed_options_during_confirmation_rejected(self):
        ui=self.open('Verify'); p=self.base/'a.bin'; p.write_bytes(b'abc')
        self.choose(ui,'verify',p,VERIFY_READ)
        ui.expected.set(hashlib.sha256(b'abc').hexdigest())
        def change(*args,**kwargs): ui.expected.set('0'*64); return True
        with patch('aeris.verify_ui.messagebox.askyesno',side_effect=change),patch('aeris.verify_ui.hash_file') as read:
            ui.run(); read.assert_not_called()
        self.assertIsNone(ui.job)
        ui.expected.set(hashlib.sha256(b'abc').hexdigest())
        with patch('aeris.verify_ui.messagebox.askyesno',return_value=True): ui.run()
        self.wait(ui); self.assertIn('Hashes correspondentes',ui.report.get('1.0','end'))
        self.assertEqual(p.read_bytes(),b'abc')
    def test_verify_cancels_old_hash_when_options_change(self):
        ui=self.open('Verify'); p=self.base/'a.bin'; p.write_bytes(b'abc')
        self.choose(ui,'verify',p,VERIFY_READ)
        def slow(*args,cancelled,progress):
            deadline=time.monotonic()+3
            while not cancelled() and time.monotonic()<deadline: time.sleep(.01)
            if cancelled(): raise Cancelled()
            raise AssertionError('not cancelled')
        with patch('aeris.verify_ui.hash_file',side_effect=slow),patch('aeris.verify_ui.messagebox.askyesno',return_value=True):
            ui.run(); self.assertIsNotNone(ui.job)
            ui.algorithm.set('SHA-512'); self.wait(ui)
        self.assertIn('Opções alteradas',ui.report.get('1.0','end'))
        self.assertEqual(float(ui.progress['value']),0)
    def test_metadata_changed_file_not_read(self):
        ui=self.open('Metadata'); p=self.base/'a.png'; q=self.base/'b.png'
        p.write_bytes(png_sample()); q.write_bytes(png_sample())
        self.choose(ui,'metadata',p,METADATA_READ)
        def change(*args,**kwargs): self.choose(ui,'metadata',q,METADATA_READ); return True
        with patch('aeris.metadata_ui.messagebox.askyesno',side_effect=change),patch('aeris.metadata_ui.inspect_file') as read:
            ui.run(); read.assert_not_called()
        self.assertIsNone(ui.job); self.assertEqual(ui.path,str(q))
    def test_metadata_visual_hiding_and_revocation(self):
        ui=self.open('Metadata'); p=self.base/'a.png'; raw=png_sample(); p.write_bytes(raw)
        self.choose(ui,'metadata',p,METADATA_READ)
        with patch('aeris.metadata_ui.messagebox.askyesno',return_value=True): ui.run()
        self.wait(ui); self.assertIn('Texto PNG: Author: Example',ui.report.get('1.0','end'))
        ui.hide_values.set(True); ui.render_result()
        report=ui.report.get('1.0','end')
        self.assertNotIn('Example',report); self.assertNotIn('Author',report)
        self.assertIn('apenas visual',report)
        ui.hide_values.set(False); ui.render_result(); self.assertIn('Example',ui.report.get('1.0','end'))
        self.h.permissions.set(METADATA_READ,False); self.assertIsNone(ui.result)
        ui.render_result(); self.assertNotIn('Example',ui.report.get('1.0','end'))
        self.assertEqual(p.read_bytes(),raw)

if __name__=='__main__': main(verbosity=2)
