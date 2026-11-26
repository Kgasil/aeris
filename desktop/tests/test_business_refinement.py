"""Synthetic Business UI regressions, no real user files or clipboard side effects."""
from pathlib import Path
from tempfile import TemporaryDirectory
from decimal import Decimal
import time
import tkinter as tk
from unittest import TestCase, main
from unittest.mock import patch
from aeris.hub import Hub
from aeris.settings import Settings
from aeris.permissions import DATA_READ,DASHBOARD_READ,REPORT_READ,REPORT_COPY
from aeris.data import profile_text,Cancelled
from aeris.dashboard import dataset_text
from aeris.calculator import calculate

class BusinessRefinement(TestCase):
    def _collect_ui(self):
        import gc
        self.h=None
        self.root=None
        gc.collect()

    def setUp(self):
        self.addCleanup(self._collect_ui)
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=tk.Tk(); self.addCleanup(self.root.destroy)
        self.h=Hub(self.root,Settings(Path(self.tmp.name)/'settings.json')); self.root.update()
    def open(self,name):
        if not self.h.enabled(name): self.h.toggle_tool(name)
        self.h.open_tool(name); self.root.update()
        return getattr(self.h,name.lower()+'_window')
    def choose(self,ui,permission):
        self.h.permissions.set(permission,True)
        path=Path(self.tmp.name)/'demo.csv'
        path.write_bytes(b'grupo,valor\nA,2\nA,2\nB,\n,4\n')
        with patch('aeris.data_ui.filedialog.askopenfilename',return_value=str(path)): ui.choose()
        return path
    def wait(self,ui):
        deadline=time.monotonic()+4
        while ui.job and time.monotonic()<deadline: self.root.update(); time.sleep(.02)
        self.assertIsNone(ui.job)
    def test_data_quality_percentages_and_changed_confirmation(self):
        ui=self.open('Data'); p=self.choose(ui,DATA_READ)
        def changed(*args,**kwargs):
            ui.delimiter.set(';'); return True
        with patch('aeris.data_ui.messagebox.askyesno',side_effect=changed),patch.object(ui,'parse') as read:
            ui.run(); read.assert_not_called()
        self.assertIsNone(ui.job)
        ui.delimiter.set(',')
        with patch('aeris.data_ui.messagebox.askyesno',return_value=True): ui.run()
        self.wait(ui)
        report=ui.report.get('1.0','end')
        self.assertIn('Células ausentes: 25.00%',report)
        self.assertIn('Duplicatas adicionais por registro: 25.00%',report)
        self.assertEqual(p.read_bytes(),b'grupo,valor\nA,2\nA,2\nB,\n,4\n')
    def test_data_options_cancel_inflight_analysis(self):
        ui=self.open('Data'); self.choose(ui,DATA_READ)
        def slow(path,delimiter,decimal,cancelled):
            end=time.monotonic()+3
            while not cancelled() and time.monotonic()<end: time.sleep(.01)
            if cancelled(): raise Cancelled()
            return profile_text('x\n1\n')
        with patch.object(ui,'parse',side_effect=slow),patch('aeris.data_ui.messagebox.askyesno',return_value=True):
            ui.run(); self.assertIsNotNone(ui.job)
            ui.decimal.set(','); self.wait(ui)
        self.assertIn('Separadores alterados',ui.report.get('1.0','end'))
        self.assertNotIn('Registros:',ui.report.get('1.0','end'))
    def test_dashboard_coverage_and_weighted_global_mean(self):
        ui=self.open('Dashboard'); self.h.permissions.set(DASHBOARD_READ,True)
        ui.render_result(dataset_text('g,v\nA,2\nA,4\nB,9\nB,\n,7\n'))
        ui.mode_box.set('Média'); ui.update_chart()
        self.assertEqual(ui.summary.overall,Decimal(5))
        report=ui.report.get('1.0','end')
        self.assertIn('Média global por registro: 5',report)
        self.assertIn('Cobertura dos registros: 60.00%',report)
        ui.decimal.set(',')
        self.assertIsNone(ui.dataset); self.assertIsNone(ui.summary); self.assertFalse(ui.canvas.find_all())
        ui.canvas.configure(height=280); self.root.update()
        self.assertFalse(ui.canvas.find_all(), 'Resize must not redraw an invalidated dataset')
        ui.render_result(dataset_text('g,v\nC,4\nD,8\n'))
        self.assertTrue(ui.canvas.find_all(), 'New valid data should draw normally')
    def test_report_rejects_changed_aggregation_before_copy(self):
        ui=self.open('Report')
        for p in (REPORT_READ,REPORT_COPY): self.h.permissions.set(p,True)
        ui.render_result(dataset_text('g,v\nA,2\nA,2\nB,\n,4\n'))
        ui.group_box.current(1); ui.mode_box.set('Soma'); ui.generate()
        self.assertIn('Cobertura dos registros: 50.00%',ui.output)
        self.assertIn('Taxa de células ausentes: 25.00%',ui.output)
        def changed(*args,**kwargs):
            ui.mode_box.set('Média'); return True
        with patch('aeris.report_ui.messagebox.askyesno',side_effect=changed),patch.object(self.root,'clipboard_clear') as clear:
            ui.copy(); clear.assert_not_called()
        self.assertIn('Média global por registro: 2',ui.output)
        self.assertIn('alterado',ui.status.get())
    def test_calculator_change_and_sample_deviation(self):
        ui=self.open('Calculator')
        ui.operation.set('Variação (%)'); ui.change_operation()
        ui.inputs[0].set('200'); ui.inputs[1].set('150'); ui.run()
        self.assertEqual(ui.result.get(),'-25%')
        ui.inputs[0].set('0'); ui.run(); self.assertFalse(ui.result.get())
        self.assertEqual(calculate('Desvio padrão amostral','2;4;6').value,Decimal(2))
        with self.assertRaises(ValueError): calculate('Desvio padrão amostral','7')
        self.assertEqual(calculate('Desvio padrão populacional','7').value,Decimal(0))
    def test_decision_rejects_matrix_changed_during_resize(self):
        ui=self.open('Decision'); ui.example(); ui.nc.set(2)
        def changed(*args,**kwargs):
            ui.criteria[2].set('Revisado'); return True
        with patch('aeris.decision_ui.messagebox.askyesno',side_effect=changed): ui.resize()
        self.assertEqual(len(ui.criteria),3); self.assertEqual(ui.nc.get(),3)
        self.assertEqual(ui.criteria[2].get(),'Revisado')
        self.assertIn('alterada',ui.status.get())
    def test_decision_reports_exact_ties_and_leader_gap(self):
        ui=self.open('Decision'); ui.example(); ui.calculate()
        self.assertIn('Diferença para a segunda:',ui.status.get())
        for row in ui.scores:
            for value in row: value.set('5')
        ui.calculate()
        self.assertIn('Empate exato na primeira posição: 3',ui.status.get())
        self.assertEqual([r.rank for r in ui.result],[1,1,1])

if __name__=='__main__': main(verbosity=2)
