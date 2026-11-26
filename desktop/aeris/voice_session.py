"""Explicit, half-duplex voice sessions; no device access in this state machine."""

MAX_TURNS=12
PHASES=('listen','chat','speak')

class VoiceSession:
    def __init__(self):
        self.stop()

    @property
    def active(self):
        return self.phase is not None

    def begin(self,model):
        if self.active or not isinstance(model,str) or not model.strip():
            raise ValueError('Sessão de voz indisponível.')
        self.model=model
        self.phase='listen'
        self.turns=0

    def advance(self,phase):
        if not self.active or phase!=self.phase:
            raise ValueError('Etapa de voz expirada.')
        if phase=='speak':
            self.turns+=1
            if self.turns>=MAX_TURNS:
                self.stop()
                return None
        self.phase=PHASES[(PHASES.index(phase)+1)%len(PHASES)]
        return self.phase

    def stop(self):
        self.phase=None
        self.model=None
        self.turns=0
