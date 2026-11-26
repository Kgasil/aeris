import unittest
from aeris.spotlight import anchor, adjacent, geometry

class SpotlightTests(unittest.TestCase):
    def test_corners(self):
        area = (0,0,1920,1040)
        self.assertEqual(anchor('Inferior direito',(36,36),area),(36,36,1872,992))
        self.assertEqual(anchor('Superior esquerdo',(36,36),area),(36,36,12,12))
        self.assertEqual(anchor('Superior direito',(36,36),area),(36,36,1872,12))
        self.assertEqual(anchor('Inferior esquerdo',(36,36),area),(36,36,12,992))

    def test_panel_above_icon(self):
        area=(0,0,1920,1040)
        icon=anchor('Inferior direito',(36,36),area)
        self.assertEqual(adjacent('Inferior direito',(320,420),icon,area),(320,420,1588,564))

    def test_panel_below_icon(self):
        area=(0,0,1920,1040)
        icon=anchor('Superior esquerdo',(36,36),area)
        self.assertEqual(adjacent('Superior esquerdo',(280,280),icon,area),(280,280,12,56))

    def test_small_screen(self):
        area=(0,0,120,100)
        self.assertEqual(anchor('Inferior direito',(240,200),area),(120,100,0,0))
        self.assertEqual(adjacent('Inferior direito',(320,420),(36,36,72,52),area),(120,100,0,0))
        self.assertEqual(geometry((120,100,0,0)),'120x100+0+0')
