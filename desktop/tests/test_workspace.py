import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.workspace import WorkspaceStore
from aeris.permissions import Permissions, WORKSPACE_OPEN
from aeris.settings import Settings, Appearance

class WorkspaceTests(unittest.TestCase):
    def test_crud_and_activation(self):
        s=WorkspaceStore(); item=s.save(' Estudos ',['Capture','Search'],['https://example.org/'])
        self.assertEqual(item.name,'Estudos'); self.assertIsNone(s.active)
        s.activate(item.name); self.assertEqual(s.active,'Estudos')
        s.save('Estudos',['Text'],[]); self.assertEqual(s.get('Estudos').tools,('Text',))
        s.delete('Estudos'); self.assertIsNone(s.active); self.assertFalse(s.list())
    def test_filter_never_activates(self):
        s=WorkspaceStore(); s.save('A',['Search','Text'],[]); s.activate('A')
        pairs=[('Capture',None),('Search',None),('Workspace',None)]
        self.assertEqual(s.filter_tools(pairs),pairs[1:]); s.activate(None); self.assertEqual(s.filter_tools(pairs),pairs)
    def test_limits_and_invalid(self):
        s=WorkspaceStore()
        for tools,links in [([],[]),(['Shell'],[]),(['Workspace'],[]),(['Text','Text'],[]),([],['file:///tmp/test']),([],['https://u:p@example.org']),([],['https://example.org']*2),([],['https://example.org/'+str(i) for i in range(9)])]:
            with self.assertRaises(ValueError): s.save('A',tools,links)
        for i in range(20): s.save(str(i),['Text'],[])
        with self.assertRaises(ValueError): s.save('Extra',['Text'],[])
        s.clear(); self.assertEqual(s.list(),()); self.assertIsNone(s.active)
    def test_permission_and_single_link(self):
        s=WorkspaceStore(); p=Permissions(); calls=[]; s.save('A',[],['https://example.org','https://example.com'])
        with self.assertRaises(PermissionError): s.open_link('A',0,p,calls.append)
        p.set(WORKSPACE_OPEN,True); s.open_link('A',1,p,calls.append)
        self.assertEqual(calls,['https://example.com'])
        with self.assertRaises(ValueError): s.open_link('A',-1,p,calls.append)
        p.set(WORKSPACE_OPEN,False)
        with self.assertRaises(PermissionError): s.open_link('A',0,p,calls.append)
        self.assertEqual(len(calls),1)
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Routine',True)
            data=json.loads(p.read_text()); data['schema']=19; del data['workspace_enabled']; p.write_text(json.dumps(data))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.routine_enabled); self.assertFalse(s.workspace_enabled)
            s.set_module('Workspace',True); s.set_appearance(Appearance(favorites=('Workspace',)))
            self.assertTrue(Settings(p).workspace_enabled); self.assertEqual(Settings(p).appearance.favorites,('Workspace',))
