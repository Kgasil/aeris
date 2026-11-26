"""Read-only, bounded-memory file hashing. No trust verdict or signature check."""
from dataclasses import dataclass
import hashlib
import hmac
import os
from pathlib import Path
import re
import stat

ALGORITHMS = {'SHA-256': 'sha256', 'SHA-512': 'sha512'}
CHUNK = 1024 * 1024
class Cancelled(Exception): pass

@dataclass(frozen=True)
class HashResult:
    algorithm: str
    digest: str
    size: int
    matches: bool | None

def expected_hash(algorithm, value):
    if algorithm not in ALGORITHMS: raise ValueError('Algoritmo não suportado.')
    value = value.strip().lower()
    if value and not re.fullmatch('[0-9a-f]{%d}' % (64 if algorithm == 'SHA-256' else 128), value):
        raise ValueError('Hash esperado deve conter somente dígitos hexadecimais na extensão correta.')
    return value

def _local_path(path):
    p = Path(path)
    if os.name == 'nt':
        import ctypes
        # Refuse UNC/device paths and non-fixed drives before opening.
        if not p.is_absolute() or any(':' in part or part == '..' for part in p.parts[1:]) or not re.fullmatch(r'[a-zA-Z]:', p.drive) or ctypes.windll.kernel32.GetDriveTypeW(p.anchor) != 3:
            raise ValueError('Selecione um arquivo em uma unidade local fixa.')
        for parent in reversed(p.parents):
            if getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400:
                raise ValueError('Caminhos com pontos de nova análise não são aceitos.')
    return p

def _stamp(st):
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns

def _regular(st):
    return stat.S_ISREG(st.st_mode) and not getattr(st, 'st_file_attributes', 0) & 0x400


def _open_read(path):
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    if os.name != 'nt':
        return os.open(path, flags)
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]; close.restype = wintypes.BOOL
    # Open existing file without following a final reparse point. Permit concurrent
    # access, but reject changed metadata/identity at both read boundaries.
    handle = create(str(path), 0x80000000, 7, None, 3, 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        _windows_identity(handle)
        return msvcrt.open_osfhandle(handle, flags)
    except BaseException:
        close(handle)
        raise


def _windows_identity(handle):
    import ctypes
    from ctypes import wintypes
    class Info(ctypes.Structure):
        _fields_ = [('attributes', wintypes.DWORD), ('created', wintypes.FILETIME), ('accessed', wintypes.FILETIME), ('written', wintypes.FILETIME), ('volume', wintypes.DWORD), ('size_high', wintypes.DWORD), ('size_low', wintypes.DWORD), ('links', wintypes.DWORD), ('index_high', wintypes.DWORD), ('index_low', wintypes.DWORD)]
    get = ctypes.WinDLL('kernel32', use_last_error=True).GetFileInformationByHandle
    get.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]; get.restype = wintypes.BOOL
    info = Info()
    if not get(handle, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    if info.attributes & (0x400 | 0x10) or not (info.index_high or info.index_low):
        raise ValueError('Identidade de arquivo regular indisponível.')
    return (info.volume, info.index_high, info.index_low, info.size_high, info.size_low, info.written.dwHighDateTime, info.written.dwLowDateTime, info.created.dwHighDateTime, info.created.dwLowDateTime)


def _matches_path(path, before, stream, initial):
    # CPython on Windows does not expose identical metadata for path stat and
    # CRT fstat. Compare like with like, and native handle identities separately.
    current = _local_path(path).lstat()
    if not _regular(current) or _stamp(before) != _stamp(current) or not _regular(initial):
        return False
    if os.name != 'nt':
        return _stamp(initial) == _stamp(current)
    import msvcrt
    if initial.st_size != current.st_size:
        return False
    fd = _open_read(path)
    try:
        same = _windows_identity(msvcrt.get_osfhandle(stream.fileno())) == _windows_identity(msvcrt.get_osfhandle(fd))
        return same and _stamp(current) == _stamp(_local_path(path).lstat())
    finally:
        os.close(fd)


def _unchanged(path, before, stream, initial):
    return _stamp(initial) == _stamp(os.fstat(stream.fileno())) and _matches_path(path, before, stream, initial)


def hash_file(path, algorithm, expected='', *, cancelled=lambda:False, progress=lambda done,total:None):
    expected = expected_hash(algorithm, expected)
    if cancelled(): raise Cancelled()
    p = _local_path(path)
    # Reject final symlinks/reparse points and non-regular files before open.
    pre = p.lstat()
    if not stat.S_ISREG(pre.st_mode) or getattr(pre, 'st_file_attributes', 0) & 0x400:
        raise ValueError('Somente arquivos regulares, sem links simbólicos ou pontos de nova análise.')
    flags = os.O_RDONLY | getattr(os,'O_BINARY',0) | getattr(os,'O_NONBLOCK',0) | getattr(os,'O_NOFOLLOW',0)
    fd = _open_read(p)
    with os.fdopen(fd,'rb') as stream:
        initial = os.fstat(stream.fileno())
        if not _matches_path(p, pre, stream, initial):
            raise ValueError('Arquivo alterado antes da leitura.')
        digest = hashlib.new(ALGORITHMS[algorithm]); done = 0
        progress(done,initial.st_size)
        while True:
            if cancelled(): raise Cancelled()
            block = stream.read(CHUNK)
            if not block: break
            done += len(block)
            if done > initial.st_size: raise ValueError('Arquivo alterado durante a leitura.')
            digest.update(block); progress(done,initial.st_size)
        if cancelled(): raise Cancelled()
        if done != initial.st_size or not _unchanged(p, pre, stream, initial):
            raise ValueError('Arquivo alterado durante a leitura; resultado descartado.')
    value = digest.hexdigest()
    return HashResult(algorithm,value,done,hmac.compare_digest(value,expected) if expected else None)
