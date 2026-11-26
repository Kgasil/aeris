"""Offline unit conversion; exact rational coefficients, rounded decimal output."""
from dataclasses import dataclass
from decimal import Decimal, Context, localcontext
from fractions import Fraction as F
from aeris.calculator import number, bounded

# Linear units expressed in their category's base unit. US gallon, international foot/pound.
UNITS = {
    'Comprimento': {'m': F(1), 'km': F(1000), 'cm': F('0.01'), 'mm': F('0.001'), 'ft': F('0.3048'), 'in': F('0.0254'), 'mi': F('1609.344')},
    'Massa': {'kg': F(1), 'g': F('0.001'), 'mg': F('0.000001'), 't': F(1000), 'lb': F('0.45359237'), 'oz': F('0.45359237')/16},
    'Área': {'m²': F(1), 'km²': F(1000000), 'cm²': F('0.0001'), 'ha': F(10000), 'ft²': F('0.3048')**2},
    'Volume': {'L': F(1), 'mL': F('0.001'), 'm³': F(1000), 'cm³': F('0.001'), 'gal US': F('3.785411784')},
    'Velocidade': {'m/s': F(1), 'km/h': F(5,18), 'mph': F('1609.344')/3600, 'nó': F(1852,3600)},
    'Pressão': {'Pa': F(1), 'kPa': F(1000), 'MPa': F(1000000), 'bar': F(100000), 'atm': F(101325), 'psi': F('0.45359237')*F('9.80665')/F('0.0254')**2},
    'Energia': {'J': F(1), 'kJ': F(1000), 'MJ': F(1000000), 'Wh': F(3600), 'kWh': F(3600000), 'cal (termoquímica)': F('4.184')},
    'Tempo': {'s': F(1), 'ms': F('0.001'), 'min': F(60), 'h': F(3600), 'dia (24 h)': F(86400)},
    'Dados': {'bit': F(1,8), 'B': F(1), 'kB': F(1000), 'MB': F(10**6), 'GB': F(10**9), 'TB': F(10**12), 'KiB': F(2**10), 'MiB': F(2**20), 'GiB': F(2**30), 'TiB': F(2**40)},
    'Temperatura': {'°C': F(1), '°F': F(5,9), 'K': F(1)},
}
# Affine conversion to kelvin: K = x * scale + offset.
TEMP_OFFSET = {'°C': F('273.15'), '°F': F('273.15')-F(32)*F(5,9), 'K': F(0)}

@dataclass(frozen=True)
class Conversion:
    value: Decimal
    unit: str
    explanation: str


def convert(category: str, source: str, target: str, text: str) -> Conversion:
    if not all(isinstance(v,str) for v in (category,source,target)):
        raise ValueError('Seleção inválida.')
    units=UNITS.get(category)
    if units is None or source not in units or target not in units:
        raise ValueError('Selecione unidades da mesma categoria.')
    x=F(number(text))
    if category=='Temperatura':
        base=x*units[source]+TEMP_OFFSET[source]
        if base<0: raise ValueError('Temperatura abaixo do zero absoluto.')
        result=(base-TEMP_OFFSET[target])/units[target]
        explanation='Conversão de temperatura absoluta via kelvin (não diferença de temperatura).'
    else:
        result=x*units[source]/units[target]
        explanation=f'Conversão linear: {source} → {target}. Fatores racionais; resultado arredondado quando necessário.'
    with localcontext(Context(prec=34,Emax=200,Emin=-200)):
        value=bounded(Decimal(result.numerator)/Decimal(result.denominator))
    return Conversion(value,target,explanation)
