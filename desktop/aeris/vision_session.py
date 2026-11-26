"""Bounded observation state; does not read the screen or contact a model."""
from time import monotonic

INTERVAL_MS=15000
MAX_SECONDS=300
MAX_FRAMES=20


class VisionSession:
    def __init__(self,clock=monotonic):
        self.clock=clock
        self.stop()

    def begin(self):
        if self.active:
            raise ValueError('Acompanhamento já ativo.')
        self.deadline=self.clock()+MAX_SECONDS
        self.frames=0

    @property
    def active(self):
        return self.deadline is not None

    def allowed(self):
        return self.active and self.clock()<self.deadline and self.frames<MAX_FRAMES

    def record(self):
        if not self.allowed():
            raise ValueError('Sessão de visão expirada.')
        self.frames+=1

    def stop(self):
        self.deadline=None
        self.frames=0
