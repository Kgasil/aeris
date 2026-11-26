"""User-created, bounded local sequences built on Bridge; no scheduler or shell."""
from dataclasses import dataclass
from aeris.bridge import Bridge, ROUTES
from aeris.permissions import ROUTINE_RUN, BRIDGE_RUN

STEPS = tuple(ROUTES)
MAX_STEPS = 5
MAX_ROUTINES = 30

@dataclass(frozen=True)
class Routine:
    name: str
    steps: tuple[str, ...]

class RoutineStore:
    def __init__(self):
        self._items = {}

    def list(self):
        return tuple(self._items.values())

    def save(self, name, steps):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80 or '\0' in name:
            raise ValueError('Nome obrigatório, até 80 caracteres.')
        name = name.strip()
        if not isinstance(steps, (list, tuple)) or not 1 <= len(steps) <= MAX_STEPS or any(s not in STEPS for s in steps):
            raise ValueError('Escolha de uma a cinco etapas suportadas.')
        if any(s != 'Expand → Text' for s in steps[:-1]):
            raise ValueError('Translate → Email e Text → Capture só podem ser a última etapa.')
        if name not in self._items and len(self._items) >= MAX_ROUTINES:
            raise ValueError('Limite de 30 rotinas por sessão.')
        item = Routine(name, tuple(steps))
        self._items[name] = item
        return item

    def delete(self, name):
        del self._items[name]

    def clear(self):
        self._items.clear()

class RoutineEngine:
    def __init__(self, hub):
        self.hub = hub
        self.bridge = Bridge(hub)

    def require(self, routine):
        if not self.hub.enabled('Routine'):
            raise PermissionError('Ative Routine no Hub.')
        self.hub.permissions.require(ROUTINE_RUN)
        for step in routine.steps:
            self.bridge.require(BRIDGE_RUN, *ROUTES[step])

    def run(self, routine, text, source_language='pt', target_language='en'):
        # Revalidate even when a caller constructs a Routine directly.
        routine = RoutineStore().save(routine.name, routine.steps)
        self.require(routine)
        results = []
        for step in routine.steps:
            preview = self.bridge.run(step, text, source_language=source_language, target_language=target_language)
            results.append(preview)
            text = preview.text
        return tuple(results)
