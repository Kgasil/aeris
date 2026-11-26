"""Bounded, local calculator. No eval, exec, file or network access."""
import ast
import re
from decimal import Decimal, DecimalException, Context, Underflow, localcontext
from dataclasses import dataclass

NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)\Z')
LITERAL = re.compile(r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z')
MAX_MAGNITUDE = Decimal('1e100')

@dataclass(frozen=True)
class Calculation:
    value: Decimal
    explanation: str
    unit: str = ''


def bounded(n):
    if not n.is_finite() or abs(n) > MAX_MAGNITUDE:
        raise ValueError('Resultado fora do limite de magnitude (10^100).')
    return n


def number(text):
    if not isinstance(text, str) or len(text) > 64 or not NUMBER.fullmatch(text.strip()):
        raise ValueError('Informe um número decimal sem separador de milhares.')
    return bounded(Decimal(text.strip().replace(',', '.')))


def expression(text):
    if not isinstance(text, str) or not text.strip() or len(text) > 256:
        raise ValueError('Expressão vazia ou acima de 256 caracteres.')
    text = text.strip().replace(',', '.')
    if not re.fullmatch(r'[0-9.()+*/%\- \t]+', text):
        raise ValueError('Use apenas números, parênteses e operadores + - * / % **.')
    try:
        tree = ast.parse(text, mode='eval')
        if sum(1 for _ in ast.walk(tree)) > 64:
            raise ValueError('Expressão complexa demais.')
        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int,float):
                literal=ast.get_source_segment(text,node)
                if not literal or len(literal)>64 or not LITERAL.fullmatch(literal):
                    raise ValueError('Número inválido.')
                return bounded(Decimal(literal))
            if isinstance(node,ast.UnaryOp) and type(node.op) in (ast.UAdd,ast.USub):
                a=visit(node.operand); return bounded(a if isinstance(node.op,ast.UAdd) else -a)
            if isinstance(node,ast.BinOp):
                a,b=visit(node.left),visit(node.right)
                op=type(node.op)
                if op is ast.Add: v=a+b
                elif op is ast.Sub: v=a-b
                elif op is ast.Mult: v=a*b
                elif op is ast.Div: v=a/b
                elif op is ast.Mod: v=a%b
                elif op is ast.Pow:
                    if b!=b.to_integral_value() or abs(b)>100: raise ValueError('Expoente inteiro entre -100 e 100.')
                    v=a**int(b)
                else: raise ValueError('Operador não permitido.')
                return bounded(v)
            raise ValueError('Expressão não permitida.')
        with localcontext(Context(prec=34,Emax=200,Emin=-200)) as ctx:
            ctx.traps[Underflow]=True
            return Calculation(visit(tree.body), 'Precedência de operadores; % = resto da divisão Decimal.')
    except (SyntaxError, DecimalException, RecursionError, OverflowError) as exc:
        raise ValueError('Expressão inválida, divisão por zero ou resultado fora dos limites.') from exc


OPERATIONS = {
    'Expressão': ('Expressão (+ - * / % **)',),
    'Raiz quadrada': ('Número',), 'Logaritmo natural': ('Número',), 'Logaritmo base 10': ('Número',),
    'Margem (%)': ('Receita', 'Custo'), 'Markup (%)': ('Receita', 'Custo'),
    'Variação (%)': ('Valor inicial positivo', 'Valor final'),
    'Juros compostos': ('Capital inicial', 'Taxa por período (%)', 'Número de períodos'),
    'Média': ('Valores separados por ponto e vírgula',),
    'Mediana': ('Valores separados por ponto e vírgula',),
    'Desvio padrão populacional': ('Valores separados por ponto e vírgula',),
    'Desvio padrão amostral': ('Valores separados por ponto e vírgula',),
}


def calculate(operation, *args):
    if operation not in OPERATIONS or len(args)!=len(OPERATIONS[operation]):
        raise ValueError('Operação ou quantidade de campos inválida.')
    if operation=='Expressão': return expression(args[0])
    try:
        with localcontext(Context(prec=34,Emax=200,Emin=-200)) as ctx:
            ctx.traps[Underflow]=True
            unit=''
            if operation in ('Média','Mediana','Desvio padrão populacional','Desvio padrão amostral'):
                text=args[0]
                if not isinstance(text,str) or len(text)>8000: raise ValueError('Lista acima do limite.')
                parts=text.split(';')
                if len(parts)>200: raise ValueError('Até 200 valores.')
                nums=sorted(number(x) for x in parts); n=len(nums); mean=sum(nums)/n
                if operation=='Média': v=mean; formula='Soma dos valores / n'
                elif operation=='Mediana': v=(nums[(n-1)//2]+nums[n//2])/2; formula='Valor central (ou média dos dois centrais)'
                elif operation=='Desvio padrão amostral':
                    if n<2: raise ValueError('Informe pelo menos dois valores para a amostra.')
                    v=(sum((x-mean)**2 for x in nums)/(n-1)).sqrt(); formula='Raiz da soma dos desvios quadráticos / (n - 1)'
                else: v=(sum((x-mean)**2 for x in nums)/n).sqrt(); formula='Raiz da soma dos desvios quadráticos / n (variância populacional)'
            else:
                vals=[number(x) for x in args]; a=vals[0]
                if operation=='Raiz quadrada': v=a.sqrt(); formula='√x'
                elif operation=='Logaritmo natural': v=a.ln(); formula='ln(x), x > 0'
                elif operation=='Logaritmo base 10': v=a.log10(); formula='log10(x), x > 0'
                elif operation in ('Margem (%)','Markup (%)'):
                    b=vals[1]
                    if a<0 or b<0: raise ValueError('Receita e custo não negativos.')
                    denominator=a if operation=='Margem (%)' else b
                    v=(a-b)/denominator*100; unit='%'; formula='(Receita - Custo) / '+('Receita' if operation=='Margem (%)' else 'Custo')+' × 100'
                elif operation=='Variação (%)':
                    if a<=0: raise ValueError('O valor inicial deve ser positivo.')
                    v=(vals[1]-a)/a*100; unit='%'; formula='(Valor final - Valor inicial) / Valor inicial × 100'
                elif operation=='Juros compostos':
                    rate,periods=vals[1:]
                    if a<0 or not -100<rate<=1000 or periods!=periods.to_integral_value() or not 0<=periods<=1200:
                        raise ValueError('Capital não negativo; taxa > -100% e até 1.000%; 0 a 1.200 períodos inteiros.')
                    v=a*(1+rate/100)**int(periods); formula='Montante = Capital × (1 + taxa/100)^períodos, sem aportes'
                else: raise ValueError('Operação inválida.')
            return Calculation(bounded(v),formula,unit)
    except DecimalException as exc:
        raise ValueError('Domínio inválido, divisão por zero ou resultado fora dos limites.') from exc


def format_value(value):
    if not value: return '0'
    # Preserve all computed significant digits; avoid enormous fixed strings.
    text=format(value,'f') if -12<=value.adjusted()<=20 else format(value,'E')
    if 'E' not in text and '.' in text: text=text.rstrip('0').rstrip('.')
    return text.replace('.',',')
