import json
import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.decision import rank_matrix, display_score
from aeris.settings import Settings, Appearance

class DecisionTests(unittest.TestCase):
    def test_example(self):
        rows=rank_matrix(['Custo','Desempenho','Facilidade'],['40','35','25'],['A','B','C'],[['9','6','8'],['6','10','7'],['8','8','9']])
        self.assertEqual([(x.name,x.score,x.rank) for x in rows],[('C',Fraction('8.25'),1),('A',Fraction('7.7'),2),('B',Fraction('7.65'),3)])
    def test_normalization(self):
        args=(['A','B'],['1','2'],['X','Y'],[['1','4'],['0','10']]); r=rank_matrix(*args)
        self.assertEqual(r,rank_matrix(args[0],['10','20'],*args[2:])); self.assertEqual(r[0].score,Fraction(20,3))
        self.assertEqual(display_score(r[0].score),'6,6667')
    def test_exact_ties_and_rounding(self):
        r=rank_matrix(['A','B'],['0,1','0,2'],['X','Y','Z'],[['1','2'],['3','1'],['0','0']]); self.assertEqual([x.rank for x in r],[1,1,3]); self.assertEqual([x.name for x in r],['X','Y','Z'])
        r=rank_matrix(['A','B'],['1','0'],['X','Y'],[['1,00001','0'],['1,00002','0']]); self.assertEqual([x.name for x in r],['Y','X']); self.assertEqual(display_score(r[0].score),display_score(r[1].score)); self.assertEqual([x.rank for x in r],[1,2])
    def test_invalid_values(self):
        for weights,scores in [(['0','0'],[['1','2'],['3','4']]),(['101','1'],[['1','2'],['3','4']]),(['-1','1'],[['1','2'],['3','4']]),(['1','1'],[['11','2'],['3','4']]),(['1','0'],[['1','NaN'],['3','4']]),(['1','1'],[['1','2'],['','4']])]:
            with self.assertRaises(ValueError): rank_matrix(['A','B'],weights,['X','Y'],scores)
    def test_dimensions_names(self):
        for criteria,weights,alternatives,scores in [(['A','a'],['1','1'],['X','Y'],[['1','2'],['3','4']]),(['A','B'],['1'],['X','Y'],[['1','2'],['3','4']]),(['A','B'],['1','1'],['X','Y'],[['1'],['3','4']]),(['A','B'],['1','1'],['X','X'],[['1','2'],['3','4']]),(['A','B'],['1','1'],['X','\x00'],[['1','2'],['3','4']]),(['A']*7,['1']*7,['X','Y'],[['1']*7]*2)]:
            with self.assertRaises(ValueError): rank_matrix(criteria,weights,alternatives,scores)
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Accessibility',True)
            data=json.loads(p.read_text()); data['schema']=43; data.pop('decision_enabled'); p.write_text(json.dumps(data))
            s=Settings(p); self.assertTrue(s.accessibility_enabled); self.assertFalse(s.decision_enabled); self.assertFalse(s.warning)
            s.set_module('Decision',True); s.set_appearance(Appearance(favorites=('Decision',))); s=Settings(p)
            self.assertTrue(s.decision_enabled and s.accessibility_enabled); self.assertEqual(s.appearance.favorites,('Decision',)); self.assertEqual(json.loads(p.read_text())['schema'],49)
