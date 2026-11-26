"""Bounded, offline Python syntax inspection. Never runs submitted code."""
import ast
import warnings
from dataclasses import dataclass

MAX_CHARS = 20_000
MAX_LINES = 1_000
MAX_NODES = 8_000
MAX_DEPTH = 100
MAX_HINTS = 50

@dataclass(frozen=True)
class Diagnostic:
    kind: str
    line: int
    column: int
    message: str
    suggestion: str

@dataclass(frozen=True)
class Analysis:
    valid: bool
    diagnostics: tuple[Diagnostic, ...]
    truncated: bool = False


def _syntax_error(exc):
    msg = exc.msg
    if isinstance(exc, IndentationError):
        tip = 'Revise o recuo do bloco e não misture tabulações com espaços.'
    elif "expected ':'" in msg:
        tip = 'Verifique os dois-pontos ao final do cabeçalho do bloco.'
    elif 'never closed' in msg or 'does not match' in msg or 'unmatched' in msg:
        tip = 'Confira a abertura e o fechamento de parênteses, colchetes e chaves.'
    elif 'unterminated string' in msg:
        tip = 'Confira as aspas de abertura e fechamento da string.'
    elif 'outside function' in msg:
        tip = 'Use return dentro de uma função; revise a estrutura e o recuo.'
    else:
        tip = 'Revise a linha indicada e as linhas anteriores; consulte a sintaxe da linguagem.'
    return Analysis(False, (Diagnostic(type(exc).__name__, exc.lineno or 1, max(1, exc.offset or 1), msg, tip),))


def analyze(source):
    if not isinstance(source, str) or not source.strip():
        raise ValueError('Informe código Python para analisar.')
    if len(source) > MAX_CHARS or source.count('\n') + source.count('\r') - source.count('\r\n') + 1 > MAX_LINES:
        raise ValueError('Limite de 20.000 caracteres e 1.000 linhas.')
    if '\x00' in source:
        raise ValueError('Código contém caractere nulo.')
    try:
        source.encode('utf-8')
    except UnicodeError as exc:
        raise ValueError('Texto Unicode inválido.') from exc
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', SyntaxWarning)
            warnings.simplefilter('ignore', DeprecationWarning)
            tree = ast.parse(source, filename='<aeris-debug>', mode='exec')
            stack = [(tree, 0)]; nodes = []
            while stack:
                node, depth = stack.pop()
                nodes.append(node)
                if len(nodes) > MAX_NODES or depth > MAX_DEPTH:
                    raise ValueError('Código excede o limite de complexidade da análise.')
                stack.extend((child, depth+1) for child in ast.iter_child_nodes(node))
            # Compile only to validate scope rules (return/break/nonlocal etc.).
            # The resulting code object is discarded, never executed.
            compile(tree, '<aeris-debug>', 'exec', dont_inherit=True)
    except SyntaxError as exc:
        return _syntax_error(exc)
    except (RecursionError, OverflowError, MemoryError) as exc:
        raise ValueError('Código excede os limites do analisador.') from exc
    hints = []
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    def add(node, kind, msg, tip):
        # AST columns are UTF-8 byte offsets; display human character columns.
        raw = lines[node.lineno-1].encode('utf-8') if node.lineno <= len(lines) else b''
        col = len(raw[:node.col_offset].decode('utf-8', errors='ignore')) + 1
        hints.append(Diagnostic(kind, node.lineno, col, msg, tip))
    for node in nodes:
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            add(node, 'Atenção', 'Except sem tipo de exceção.', 'Considere capturar exceções específicas; um except amplo pode ocultar falhas.')
        elif isinstance(node, ast.ImportFrom) and any(alias.name == '*' for alias in node.names):
            add(node, 'Atenção', 'Importação com asterisco.', 'Considere importar nomes explicitamente para reduzir ambiguidades.')
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = [*node.args.defaults, *node.args.kw_defaults]
            for default in defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    add(default, 'Atenção', 'Valor padrão mutável.', 'Considere usar None como padrão e criar o objeto dentro da função.')
    hints.sort(key=lambda d: (d.line, d.column, d.message))
    return Analysis(True, tuple(hints[:MAX_HINTS]), len(hints)>MAX_HINTS)
