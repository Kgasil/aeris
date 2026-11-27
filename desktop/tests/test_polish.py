import unittest
import tkinter as tk
from tkinter import ttk
from aeris.polish import compact_workspace, COMPACT_WIDTH, contrast_ratio
from aeris.theme import PALETTES, configure, apply_tree


class PolishTests(unittest.TestCase):
    def test_breakpoint(self):
        self.assertTrue(compact_workspace(COMPACT_WIDTH-1))
        self.assertFalse(compact_workspace(COMPACT_WIDTH))
        self.assertFalse(compact_workspace(COMPACT_WIDTH+1))

    def test_contrast_reference(self):
        self.assertAlmostEqual(contrast_ratio('#000000','#FFFFFF'),21.0)
        self.assertEqual(contrast_ratio('#FFFFFF','#FFFFFF'),1.0)

    def test_text_contrast(self):
        for name,p in PALETTES.items():
            for fg in ('deep','secondary'):
                for bg in ('air','soft','field'):
                    with self.subTest(theme=name,foreground=fg,background=bg):
                        self.assertGreaterEqual(contrast_ratio(p[fg],p[bg]),4.5)
            self.assertGreaterEqual(contrast_ratio(p['select_text'],p['selected']),4.5)

    def test_focus_contrast(self):
        for p in PALETTES.values():
            for bg in ('air','soft','field'):
                self.assertGreaterEqual(contrast_ratio(p['focus'],p[bg]),3.0)

    def test_shared_semantic_contrast(self):
        for name,p in PALETTES.items():
            pairs=[['primary_text','primary'],['primary_text','primary_hover'],['sidebar_text','sidebar'],['sidebar_text','sidebar_hover'],['sidebar_muted','sidebar'],['nav_text','nav_selected'],['success','air'],['success','soft'],['success','field'],['info','air'],['info','soft'],['info','field'],['warning','air'],['warning','soft'],['warning','field'],['danger','air'],['danger','soft'],['danger','field'],['deep','air'],['deep','soft'],['deep','field'],['secondary','air'],['secondary','soft'],['secondary','field']]
            for fg,bg in pairs:
                with self.subTest(theme=name,foreground=fg,background=bg):
                    self.assertGreaterEqual(contrast_ratio(p[fg],p[bg]),4.5)

    def test_primary_contrast(self):
        for bg in ('#30694F','#285640','#397557'):
            self.assertGreaterEqual(contrast_ratio('#FFFFFF',bg),4.5)


class PolishTkTests(unittest.TestCase):
    def setUp(self):
        try: self.root=tk.Tk()
        except tk.TclError as exc: self.skipTest(str(exc))
        self.root.withdraw()
        self.addCleanup(self.root.destroy)

    def test_focus_and_secondary_style(self):
        style=ttk.Style(self.root)
        for name,p in PALETTES.items():
            configure(self.root,name)
            self.assertEqual(style.lookup('TEntry','bordercolor',('focus',)),p['focus'])
            self.assertEqual(style.lookup('TButton','focuscolor',('focus',)),p['focus'])
            self.assertEqual(style.lookup('Aeris.Muted.TLabel','foreground'),p['secondary'])

    def test_shared_styles_follow_theme(self):
        style=ttk.Style(self.root)
        for name,p in PALETTES.items():
            configure(self.root,name)
            self.assertEqual(style.lookup('Experience.Side.TFrame','background'),p['sidebar'])
            self.assertEqual(style.lookup('Experience.Active.TButton','foreground'),p['nav_text'])
            self.assertEqual(style.lookup('Experience.Primary.TButton','background'),p['primary'])
            self.assertEqual(style.lookup('Aeris.Stop.TButton','foreground'),p['danger'])

    def test_theme_roundtrip_preserves_text(self):
        frame=tk.Frame(self.root,bg='#DCEFE3')
        editor=tk.Text(frame)
        editor.insert('1.0','Rascunho fictício')
        for name in ('Claro','Escuro','Claro'):
            p=configure(self.root,name)
            apply_tree(self.root,name)
            self.assertEqual(frame.cget('bg'),p['soft'])
            self.assertEqual(editor.cget('bg'),p['field'])
            self.assertEqual(editor.cget('highlightcolor'),p['focus'])
            self.assertEqual(editor.get('1.0','end-1c'),'Rascunho fictício')


if __name__=='__main__':
    unittest.main()
