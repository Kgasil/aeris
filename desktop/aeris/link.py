"""Offline URL structure inspection. Never resolves, visits or authenticates a URL."""
from dataclasses import dataclass
import ipaddress
import re
import unicodedata
from urllib.parse import urlsplit, unquote_plus

LIMIT = 4096

@dataclass(frozen=True)
class Inspection:
    host: str
    scheme: str
    indicators: tuple[str, ...]


def inspect_url(value: str) -> Inspection:
    if not isinstance(value, str) or not value or len(value) > LIMIT:
        raise ValueError('Informe uma URL de até 4.096 caracteres.')
    if any(c.isspace() or unicodedata.category(c).startswith('C') for c in value) or '\\' in value:
        raise ValueError('URL com espaço, caractere invisível/de controle ou barra invertida. Não abra sem revisão.')
    try:
        p = urlsplit(value)
        host = p.hostname
        port = p.port
    except ValueError:
        raise ValueError('Estrutura de URL inválida ou ambígua.') from None
    if p.scheme not in ('http', 'https') or not host or not p.netloc:
        raise ValueError('Somente URLs HTTP/HTTPS completas são analisadas.')
    if '%' in host or p.netloc.count('@') > 1 or p.netloc.endswith(':'):
        raise ValueError('Autoridade ambígua ou codificada. Não abra sem revisão.')
    authority = p.netloc.rsplit('@', 1)[-1]
    if authority.startswith('[') and not re.fullmatch(r'\[[^\[\]]+\](?::[0-9]+)?', authority):
        raise ValueError('Autoridade IPv6 inválida ou ambígua.')
    notes = []
    if p.scheme == 'http': notes.append('HTTP: a conexão não usa HTTPS.')
    if '@' in p.netloc: notes.append('Informação de usuário antes de @: o destino real é o host mostrado abaixo, não o texto anterior.')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        canonical = address.compressed
        notes.append('Endereço IP literal em vez de nome de domínio.')
        if not address.is_global: notes.append('IP não global: pode apontar para uma rede local ou endereço reservado.')
    else:
        if '[' in p.netloc or ']' in p.netloc:
            raise ValueError('Host entre colchetes não reconhecido.')
        try:
            canonical = host.encode('idna').decode('ascii').lower()
        except UnicodeError:
            raise ValueError('Nome de domínio inválido.') from None
        labels = canonical.rstrip('.').split('.')
        if len(canonical.rstrip('.')) > 253 or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in labels) or canonical.endswith('..'):
            raise ValueError('Nome de domínio inválido ou ambíguo.')
        if any(ord(c)>127 for c in host) or any(x.startswith('xn--') for x in labels):
            notes.append('Domínio internacionalizado: a representação ASCII usa IDNA da biblioteca Python e pode divergir do navegador. Compare a grafia com a origem oficial.')
        if len(labels) == 1: notes.append('Host sem domínio público aparente; pode ser interno ou um IP em formato alternativo.')
        if re.fullmatch(r'(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*\.?', canonical):
            notes.append('Host numérico não canônico: navegadores podem interpretá-lo como um IP diferente.')
        if len(labels) >= 5: notes.append('Muitos níveis no nome do host; confira o domínio oficial por outra fonte.')
        if canonical.endswith('.'): notes.append('Host com ponto final; confira a grafia e a origem.')
    if port is not None and port != (443 if p.scheme == 'https' else 80):
        notes.append('Porta diferente da padrão do protocolo.')
    if re.search(r'%[0-9a-fA-F]{2}', p.path): notes.append('Caminho com caracteres codificados; pode ser legítimo, mas dificulta a leitura.')
    keys = {unquote_plus(item.partition('=')[0]).casefold() for item in p.query.split('&')}
    if keys & {'token','access_token','password','passwd','secret','api_key','session','sessionid','auth','code'}:
        notes.append('Parâmetro com nome associado a credenciais ou sessão; evite compartilhar a URL.')
    if p.fragment:
        notes.append('Fragmento presente: pode conter parâmetros ou dados sensíveis; não compartilhe sem revisar.')
    if re.search(r'%(?![0-9a-fA-F]{2})',p.path+'?'+p.query+'#'+p.fragment):
        notes.append('Sequência percentual incompleta ou inválida; interpretação pode variar.')
    return Inspection(canonical, p.scheme, tuple(notes))
