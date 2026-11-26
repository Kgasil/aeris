"""Session-only workspace presets; no automatic opening or module activation."""
from dataclasses import dataclass
from aeris.settings import FAVORITES
from aeris.bookmarks import validate_url, launch_windows
from aeris.permissions import WORKSPACE_OPEN

TOOLS = tuple(n for n in FAVORITES if n != 'Workspace')
MAX_WORKSPACES = 20
MAX_LINKS = 8

@dataclass(frozen=True)
class Workspace:
    name: str
    tools: tuple[str, ...]
    links: tuple[str, ...]

class WorkspaceStore:
    def __init__(self):
        self._items = {}
        self.active = None

    def list(self): return tuple(self._items.values())
    def get(self, name): return self._items[name]

    def save(self, name, tools, links):
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80 or any(ord(c) < 32 for c in name):
            raise ValueError('Nome obrigatório, até 80 caracteres.')
        name = name.strip()
        if not isinstance(tools, (list, tuple)) or any(not isinstance(n, str) or n not in TOOLS for n in tools) or len(set(tools)) != len(tools):
            raise ValueError('Selecione ferramentas válidas, sem duplicatas.')
        if not isinstance(links, (list, tuple)) or len(links) > MAX_LINKS:
            raise ValueError('Até oito endereços por ambiente.')
        links = tuple(validate_url(x) for x in links)
        if len(set(links)) != len(links): raise ValueError('Endereços duplicados.')
        if not tools and not links: raise ValueError('Escolha pelo menos uma ferramenta ou um link.')
        if name not in self._items and len(self._items) >= MAX_WORKSPACES: raise ValueError('Limite de 20 ambientes.')
        item = Workspace(name, tuple(tools), links)
        self._items[name] = item
        return item

    def activate(self, name):
        if name is not None: self.get(name)
        self.active = name

    def delete(self, name):
        del self._items[name]
        if self.active == name: self.active = None

    def clear(self):
        self._items.clear(); self.active = None

    def filter_tools(self, tools):
        if self.active is None: return tools
        selected = set(self.get(self.active).tools)
        # Workspace remains reachable even with an empty selection.
        return [pair for pair in tools if pair[0] in selected or pair[0] == 'Workspace']

    def open_link(self, name, index, permissions, launcher=launch_windows):
        permissions.require(WORKSPACE_OPEN)
        links = self.get(name).links
        if type(index) is not int or not 0 <= index < len(links): raise ValueError('Escolha um link salvo.')
        return launcher(validate_url(links[index]))
