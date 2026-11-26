"""Bounded input at trust boundaries. Not an OS sandbox."""
import json
import math
import os
import stat
from aeris.verify import _local_path, _open_read, _matches_path, _unchanged


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Chave JSON duplicada.')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Constante JSON não permitida.')


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Número JSON não finito.')
    return result


def check_depth(value, depth=0):
    if depth > 32:
        raise ValueError('JSON excessivamente aninhado.')
    if isinstance(value, dict):
        for item in value.values(): check_depth(item, depth+1)
    elif isinstance(value, list):
        for item in value: check_depth(item, depth+1)


def strict_json(raw, limit):
    if not isinstance(raw, (str, bytes)) or len(raw) > limit:
        raise ValueError('JSON acima do limite ou inválido.')
    try:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        elif len(raw.encode('utf-8')) > limit:
            raise ValueError('JSON acima do limite.')
        value = json.loads(raw, object_pairs_hook=unique_pairs, parse_constant=reject_constant, parse_float=finite_float)
        check_depth(value)
        return value
    except (RecursionError, UnicodeError) as exc:
        raise ValueError('JSON inválido ou excessivamente aninhado.') from exc


def bounded_read(path, limit):
    p = _local_path(path)
    before = p.lstat()
    if not stat.S_ISREG(before.st_mode) or getattr(before, 'st_file_attributes', 0) & 0x400:
        raise ValueError('Somente arquivos regulares locais, sem links.')
    if before.st_size > limit:
        raise ValueError('Arquivo excede o limite permitido.')
    flags = os.O_RDONLY | getattr(os,'O_BINARY',0) | getattr(os,'O_NONBLOCK',0) | getattr(os,'O_NOFOLLOW',0)
    with os.fdopen(_open_read(p), 'rb') as stream:
        initial = os.fstat(stream.fileno())
        if not _matches_path(p, before, stream, initial):
            raise ValueError('Arquivo alterado antes da leitura.')
        raw = stream.read(limit + 1)
        if len(raw) > limit or len(raw) != initial.st_size or not _unchanged(p, before, stream, initial):
            raise ValueError('Arquivo acima do limite ou alterado durante a leitura.')
    return raw
