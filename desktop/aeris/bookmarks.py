"""Protected bookmark records. Explicit browser handoff, no network or fetching."""
from dataclasses import dataclass
from urllib.parse import urlsplit
import ipaddress
import json
from aeris.safe_input import strict_json
import os
import re
import unicodedata
from aeris.registry import normalize
from aeris.vault import Vault
from aeris.permissions import OPEN_BOOKMARK


def validate_url(url):
    if not isinstance(url, str) or not 1 <= len(url) <= 4096 or any(c.isspace() or unicodedata.category(c).startswith('C') for c in url) or '\\' in url:
        raise ValueError('Endereço inválido. Use URL HTTP ou HTTPS completa.')
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username is not None or parts.password is not None or '%' in parts.netloc:
        raise ValueError('Somente HTTP/HTTPS, sem credenciais no endereço.')
    host = parts.hostname
    if ':' in host:
        ipaddress.IPv6Address(host)
    else:
        ascii_host = host.rstrip('.').encode('idna').decode('ascii')
        if not ascii_host or len(ascii_host)>253 or any(not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', label) for label in ascii_host.split('.')):
            raise ValueError('Nome de host inválido.')
    if parts.port is not None and not 1 <= parts.port <= 65535:
        raise ValueError('Porta inválida.')
    return url

@dataclass(frozen=True)
class Bookmark:
    id: int
    title: str
    category: str
    url: str


def validate_fields(title, category, url):
    if not isinstance(title,str) or not 1<=len(title.strip())<=120 or not isinstance(category,str) or not 1<=len(category.strip())<=60:
        raise ValueError('Título (1–120) e categoria (1–60) obrigatórios.')
    return title.strip(), category.strip(), validate_url(url)


def launch_windows(url):
    if os.name != 'nt': raise OSError('Abertura nativa requer Windows.')
    os.startfile(validate_url(url))

class BookmarkStore:
    def __init__(self, path, permissions, backend=None, launcher=None):
        self.vault = Vault(path, backend)
        self.permissions = permissions
        self.launcher = launcher if launcher is not None else launch_windows

    @property
    def unlocked(self): return self.vault.unlocked

    def unlock(self):
        self.vault.unlock()
        try: self.list()
        except Exception:
            self.lock(); raise

    def lock(self): self.vault.lock()

    def list(self, query='', category=None):
        items=[]; words=normalize(query).split()
        for entry in self.vault.list():
            data=strict_json(entry.body, 80000)
            if not isinstance(data,dict) or set(data)!= {'category','url'}: raise ValueError('Registro de link inválido.')
            title, cat, url=validate_fields(entry.title,data['category'],data['url'])
            if (category is None or cat==category) and all(w in normalize(f'{title} {cat} {url}') for w in words):
                items.append(Bookmark(entry.id,title,cat,url))
        return tuple(items)

    def get(self, item_id):
        for item in self.list():
            if item.id==item_id: return item
        raise KeyError(item_id)

    def save(self,title,category,url,item_id=None):
        title,category,url=validate_fields(title,category,url)
        if any(x.url==url and x.id!=item_id for x in self.list()): raise ValueError('Este endereço já está salvo.')
        entry=self.vault.save(title,json.dumps({'category':category,'url':url},ensure_ascii=False),item_id)
        return Bookmark(entry.id,title,category,url)

    def delete(self,item_id): self.vault.delete(item_id)

    def open(self,item_id):
        self.permissions.require(OPEN_BOOKMARK)
        item=self.get(item_id)
        self.launcher(validate_url(item.url))
