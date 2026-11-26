import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.calculator import calculate, expression, format_value, number
from aeris.settings import Settings, Appearance, FLAGS

class CalculatorTests(unittest.TestCase):
    def test_expression_precedence(self):
        for text,expected in [('2+3*4','14'),('(2+3)*4','20'),('2**3**2','512'),('-2**2','-4'),('5%2','1'),('0,1+0,2','0.3'),('2**-3','0.125')]:
            with self.subTest(text=text): self.assertEqual(expression(text).value,Decimal(expected))
    def test_rejected_syntax(self):
        for text in ['__import__("os")','open(1)','[1]','1//2','1<<2','1,2,3','1;2','0x10','2e4','1\n+2','1.__class__','(1)(2)']:
            with self.subTest(text=text),self.assertRaises(ValueError):expression(text)
    def test_domain_and_limits(self):
        for text in ['1/0','0**-1','2**101','2**0.5','(10**100)*10','9'*65,'1+'*40+'1','('*129+'1'+')'*129]:
            with self.subTest(text=text),self.assertRaises(ValueError):expression(text)
        for op,value in [('Raiz quadrada','-1'),('Logaritmo natural','0'),('Logaritmo base 10','-5')]:
            with self.assertRaises(ValueError):calculate(op,value)
    def test_science(self):
        self.assertEqual(calculate('Raiz quadrada','2,25').value,Decimal('1.5'))
        self.assertEqual(calculate('Logaritmo natural','1').value,0)
        self.assertEqual(calculate('Logaritmo base 10','1000').value,3)
    def test_finance(self):
        self.assertEqual(calculate('Margem (%)','15000','10000').value.quantize(Decimal('.01')),Decimal('33.33'))
        self.assertEqual(calculate('Markup (%)','15000','10000').value,50)
        self.assertEqual(calculate('Juros compostos','1000','10','2').value,1210)
        self.assertEqual(calculate('Juros compostos','1000','-10','2').value,810)
        for op,args in [('Margem (%)',('0','1')),('Markup (%)',('1','0')),('Juros compostos',('1','-100','1')),('Juros compostos',('1','1','1.5')),('Juros compostos',('1','1','1201'))]:
            with self.assertRaises(ValueError):calculate(op,*args)
    def test_statistics(self):
        self.assertEqual(calculate('Média','1;2;3').value,2)
        self.assertEqual(calculate('Mediana','4;1;2;3').value,Decimal('2.5'))
        self.assertEqual(calculate('Desvio padrão populacional','1;3').value,1)
        self.assertEqual(calculate('Desvio padrão populacional','7').value,0)
        for text in ['', '1;;3','1;'*200+'1','NaN;2']:
            with self.assertRaises(ValueError):calculate('Média',text)
    def test_format_and_numbers(self):
        self.assertEqual(format_value(Decimal('123.4500')),'123,45')
        self.assertEqual(format_value(Decimal('1E+100')),'1E+100')
        self.assertEqual(format_value(Decimal('-0')),'0')
        for text in ['NaN','Infinity','1.000,00','1_000','1e3']:
            with self.assertRaises(ValueError):number(text)
    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json';s=Settings(p);s.set_module('Report',True)
            old=json.loads(p.read_text());old['schema']=37;old.pop('calculator_enabled');p.write_text(json.dumps(old))
            s=Settings(p);self.assertTrue(s.report_enabled);self.assertFalse(s.calculator_enabled)
            s.set_module('Calculator',True);s.set_appearance(Appearance(favorites=('Calculator',)))
            s=Settings(p);self.assertTrue(s.calculator_enabled);self.assertEqual(s.appearance.favorites,('Calculator',));self.assertEqual(json.loads(p.read_text())['schema'],49)
