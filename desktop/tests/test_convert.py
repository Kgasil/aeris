import json
import unittest
from decimal import Decimal
from tempfile import TemporaryDirectory
from pathlib import Path
from aeris.convert import convert, UNITS
from aeris.settings import Settings, Appearance, FLAGS

class ConvertTests(unittest.TestCase):
    def assert_conversion(self,category,source,target,text,expected):
        self.assertEqual(convert(category,source,target,text).value,Decimal(expected))
    def test_length_mass_area_volume(self):
        for args in [('Comprimento','in','cm','1','2.54'),('Massa','lb','kg','1','0.45359237'),('Área','ha','m²','2','20000'),('Volume','gal US','L','1','3.785411784')]:self.assert_conversion(*args)
    def test_speed_pressure_energy_time(self):
        for args in [('Velocidade','km/h','m/s','36','10'),('Pressão','atm','Pa','1','101325'),('Energia','kWh','J','1','3600000'),('Tempo','dia (24 h)','h','2','48')]:self.assert_conversion(*args)
        self.assertAlmostEqual(float(convert('Pressão','psi','Pa','1').value),6894.757293168,places=8)
    def test_temperature(self):
        for args in [('Temperatura','°C','°F','0','32'),('Temperatura','°F','°C','-40','-40'),('Temperatura','°C','K','-273,15','0'),('Temperatura','°F','K','-459,67','0'),('Temperatura','K','°C','0','-273.15'),('Temperatura','°F','°C','212','100')]:self.assert_conversion(*args)
        for unit,text in [('K','-0.0001'),('°C','-273.15001'),('°F','-459.67001')]:
            with self.assertRaises(ValueError):convert('Temperatura',unit,unit,text)
    def test_digital(self):
        for args in [('Dados','MiB','B','1','1048576'),('Dados','MB','B','1','1000000'),('Dados','B','bit','1','8'),('Dados','GiB','MiB','1','1024')]:self.assert_conversion(*args)
    def test_signed_and_repeating(self):
        self.assert_conversion('Comprimento','m','cm','-1,25','-125')
        self.assert_conversion('Tempo','s','min','1','0.01666666666666666666666666666666667')
        self.assert_conversion('Massa','kg','kg','0','0')
    def test_invalid(self):
        for text in ('','NaN','inf','1e999','1.000,00','2+3','1'*65):
            with self.assertRaises(ValueError):convert('Dados','B','MB',text)
        for args in [('Dados','kg','B','1'),('Inexistente','a','b','1'),('Dados','B',None,'1')]:
            with self.assertRaises(ValueError):convert(*args)
    def test_all_units_identity_and_round_trip(self):
        for cat,units in UNITS.items():
            for u in units:self.assert_conversion(cat,u,u,'42','42')
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Calculator',True)
            data=json.loads(p.read_text());data['schema']=38;data.pop('convert_enabled');p.write_text(json.dumps(data))
            s=Settings(p);self.assertTrue(s.calculator_enabled);self.assertFalse(s.convert_enabled)
            s.set_module('Convert',True);s.set_appearance(Appearance(favorites=('Convert',)))
            s=Settings(p);self.assertTrue(s.convert_enabled and s.calculator_enabled);self.assertEqual(s.appearance.favorites,('Convert',));self.assertEqual(json.loads(p.read_text())['schema'],49)
