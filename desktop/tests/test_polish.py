import unittest
import tkinter as tk
from tkinter import ttk
from aeris.polish import compact_workspace, COMPACT_WIDTH, contrast_ratio
from aeris.theme import PALETTES, configure, apply_tree, set_window_icon


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
            for control in ('TRadiobutton','TCheckbutton','Experience.Goal.TRadiobutton','Treeview'):
                self.assertEqual(style.lookup(control,'focuscolor',('focus',)),p['focus'])
            self.assertEqual(style.lookup('Aeris.Muted.TLabel','foreground'),p['secondary'])

    def test_shared_styles_follow_theme(self):
        style=ttk.Style(self.root)
        for name,p in PALETTES.items():
            configure(self.root,name)
            self.assertEqual(style.lookup('Experience.Side.TFrame','background'),p['sidebar'])
            self.assertEqual(style.lookup('Experience.Active.TButton','foreground'),p['nav_text'])
            self.assertEqual(style.lookup('Experience.Primary.TButton','background'),p['primary'])
            self.assertEqual(style.lookup('Aeris.Stop.TButton','foreground'),p['danger'])

    def test_scrollbar_palette_roundtrip(self):
        style=ttk.Style(self.root)
        canvas=tk.Canvas(self.root)
        vertical=ttk.Scrollbar(self.root, orient='vertical', command=canvas.yview)
        horizontal=ttk.Scrollbar(self.root, orient='horizontal', command=canvas.xview)
        commands=(vertical.cget('command'), horizontal.cget('command'))
        for name in ('Escuro','Claro','Escuro'):
            p=configure(self.root,name)
            for control in ('Vertical.TScrollbar','Horizontal.TScrollbar'):
                self.assertEqual(style.lookup(control,'background'),p['forest'])
                self.assertEqual(style.lookup(control,'troughcolor'),p['soft'])
                self.assertEqual(style.lookup(control,'background',('active',)),p['primary_hover'])
                self.assertEqual(style.lookup(control,'background',('pressed',)),p['primary'])
                self.assertGreaterEqual(contrast_ratio(p['forest'],p['soft']),3.0)
            self.assertEqual((vertical.cget('command'),horizontal.cget('command')),commands)

    def test_official_native_window_icon(self):
        if self.root.tk.call('tk','windowingsystem') == 'win32':
            self.assertTrue(set_window_icon(self.root))
        else:
            self.assertFalse(set_window_icon(self.root))

    def test_scroll_canvas_focus_outline_preserves_contents(self):
        scroll=tk.Canvas(self.root,highlightthickness=1,takefocus=True)
        scroll._aeris_scroll=True
        item=scroll.create_rectangle(2,3,20,30,fill='#123456')
        preview=tk.Canvas(self.root,bg='#102030')
        for name in ('Escuro','Claro','Escuro'):
            p=configure(self.root,name)
            apply_tree(self.root,name)
            self.assertEqual(scroll.cget('highlightbackground'),p['muted'])
            self.assertEqual(scroll.cget('highlightcolor'),p['focus'])
            self.assertEqual(scroll.itemcget(item,'fill'),'#123456')
            self.assertEqual(preview.cget('bg'),'#102030')

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
