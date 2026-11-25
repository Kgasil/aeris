import unittest
from aeris.quick_panel import panel_bounds

class QuickPanelTests(unittest.TestCase):
    def test_bottom_right(self):
        self.assertEqual(panel_bounds('Inferior direito', (320,420), (100,100,800,600), (1920,1080)),
                         (320,420,580,280))

    def test_clamp(self):
        self.assertEqual(panel_bounds('Superior esquerdo', (420,520), (-100,-200,500,500), (300,400)),
                         (300,400,0,0))
