import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from aeris.dashboard import dataset_text,dataset_file
from aeris.report import build_report
from aeris.settings import Settings,Appearance
from aeris.permissions import Permissions,REPORT_READ,REPORT_COPY,DATA_READ

class ReportTests(unittest.TestCase):
    def setUp(self):
        self.dataset=dataset_text('grupo;valor\nA;2,5\nA;2,5\nB;-1\nB;\n;3\n',';',',')
    def test_quality(self):
        text=build_report(self.dataset)
        self.assertIn('Registros: 5 | Colunas: 2',text)
        self.assertIn('Células ausentes: 2 | Duplicatas exatas adicionais: 1',text)
        self.assertIn('Agregação não selecionada.',text)
        self.assertIn('Investigue as duplicatas',text)
    def test_aggregation(self):
        text=build_report(self.dataset,0,'Soma',1)
        self.assertIn('Registros usados: 3 | Ignorados: 2 | Categorias: 2',text)
        self.assertIn('Total global: 4.0',text)
        self.assertIn('- B: -1 (1 registros)',text)
        self.assertIn('Média global por registro: 1.33333333333',build_report(self.dataset,0,'Média',1))
    def test_empty_and_invalid(self):
        text=build_report(dataset_text('grupo,valor\n,\n'),0)
        self.assertIn('Total global: —',text)
        self.assertIn('Nenhuma categoria válida.',text)
        with self.assertRaises(ValueError):build_report(self.dataset,0,'Soma',0)
        with patch('aeris.dashboard.MAX_GROUPS',1),self.assertRaises(ValueError):build_report(self.dataset,0)
    def test_control_characters_and_long_names(self):
        d=dataset_text('grupo,valor\n"x\ny",1\n'+('z'*150)+',2\n')
        text=build_report(d,0)
        self.assertIn('x\\u000ay',text); self.assertNotIn('z'*150,text); self.assertIn('…',text)
    def test_file_and_permissions(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/'x.csv';raw=b'g,v\na,2\n';p.write_bytes(raw)
            self.assertIn('Total global: 2',build_report(dataset_file(p),0,'Soma',1));self.assertEqual(p.read_bytes(),raw)
        grants=Permissions();grants.set(DATA_READ,True);self.assertFalse(grants.allowed(REPORT_READ));grants.set(REPORT_READ,True);self.assertFalse(grants.allowed(REPORT_COPY))
    def test_migration(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/'settings.json';s=Settings(p);s.set_module('Dashboard',True)
            old=json.loads(p.read_text());old['schema']=36;old.pop('report_enabled');p.write_text(json.dumps(old));s=Settings(p)
            self.assertTrue(s.dashboard_enabled);self.assertFalse(s.report_enabled);self.assertFalse(s.warning)
            s.set_module('Report',True);s.set_appearance(Appearance(favorites=('Report',)));self.assertTrue(Settings(p).report_enabled)
