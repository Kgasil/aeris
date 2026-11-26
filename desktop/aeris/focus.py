"""Session-only focus timer; no monitoring of user activity."""
from math import ceil
from time import monotonic

MODES = ('Concentração', 'Intervalo')


class FocusTimer:
    def __init__(self, clock=monotonic):
        self.clock = clock
        self.mode = MODES[0]
        self.minutes = 25
        self.state = 'ready'
        self.remaining = 25 * 60.0
        self.deadline = None
        self.completed = dict.fromkeys(MODES, 0)

    def configure(self, mode, minutes):
        if self.state in ('running', 'paused'):
            raise ValueError('Reinicie a sessão antes de configurar.')
        if mode not in MODES or type(minutes) is not int or not 1 <= minutes <= 120:
            raise ValueError('Selecione de 1 a 120 minutos.')
        self.mode, self.minutes = mode, minutes
        self.reset()

    def start(self):
        if self.state == 'finished':
            self.reset()
        if self.state not in ('ready', 'paused'):
            return
        self.deadline = self.clock() + self.remaining
        self.state = 'running'

    def tick(self):
        """Return True only on the transition to a completed interval."""
        if self.state != 'running':
            return False
        self.remaining = max(0.0, self.deadline - self.clock())
        if self.remaining == 0:
            self.state = 'finished'
            self.deadline = None
            self.completed[self.mode] += 1
            return True
        return False

    def pause(self):
        finished = self.tick()
        if self.state == 'running':
            self.state = 'paused'
            self.deadline = None
        return finished

    def reset(self):
        self.state = 'ready'
        self.deadline = None
        self.remaining = float(self.minutes * 60)

    @property
    def seconds(self):
        return ceil(self.remaining)
