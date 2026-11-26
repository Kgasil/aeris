"""Bind a spoken question to one explicitly reviewed image; no device access."""
from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class VisualQuestion:
    image: bytes
    model: str

    def matches(self, image, model):
        return self.image is image and self.model == model

    def draft(self, text, image, model, *, mic_allowed, screen_allowed, empty_editor):
        if not self.matches(image, model) or not mic_allowed or not screen_allowed or not empty_editor:
            raise ValueError('Captura, modelo, permissão ou rascunho mudou.')
        if not isinstance(text, str) or not text.strip() or len(text) > 4000 or '\0' in text:
            raise ValueError('Pergunta inválida.')
        return text.strip()
