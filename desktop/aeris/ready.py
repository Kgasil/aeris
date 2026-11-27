"""Readiness checks: no downloads, device capture or unsolicited network access."""
from dataclasses import dataclass
import importlib.util
import re
import sys

TEST_PROMPT = 'Responda com uma saudação curta em português.'


@dataclass(frozen=True)
class Readiness:
    windows: bool
    source: bool
    optional_missing: tuple

    @property
    def loopback_candidate(self):
        return self.windows and self.source and not self.optional_missing


def inspect_environment(*, platform=None, frozen=None, find_spec=importlib.util.find_spec):
    platform=sys.platform if platform is None else platform
    frozen=bool(getattr(sys,'frozen',False)) if frozen is None else frozen
    missing=[]
    if platform=='win32' and not frozen:
        for name in ('soundcard','numpy','faster_whisper'):
            try:
                if find_spec(name) is None: missing.append(name)
            except (ImportError,ValueError,AttributeError):
                missing.append(name)
    return Readiness(platform=='win32',not frozen,tuple(missing))


def model_selection(current, models):
    """Never silently replace a user's existing selection."""
    if current.strip():
        return current
    return models[0] if len(models)==1 else ''


def check_model(model, *, chat_fn):
    """A fixed, synthetic request; no user history, screen or files."""
    if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}',model) or 'cloud' in model.lower():
        raise ValueError('Escolha um modelo local válido.')
    response=chat_fn(model, (), TEST_PROMPT)
    if not isinstance(response,str) or not response.strip() or len(response)>4000:
        raise ValueError('Resposta de teste inválida.')
    return True
