"""Apply the reviewable Windows compatibility patch to the original RC1 source."""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
base = root / 'desktop' / 'aeris'

def edit(path, old, new):
    s = path.read_text(encoding='utf-8')
    if s.count(old) != 1:
        raise RuntimeError(f'Unexpected original content: {path}: {old[:100]}')
    path.write_text(s.replace(old, new), encoding='utf-8')

helper = '''def _regular(st):
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


'''
edit(base/'verify.py', 'def hash_file(', helper+'def hash_file(')
edit(base/'verify.py', 'fd = os.open(p,flags)', 'fd = _open_read(p)')
edit(base/'verify.py', 'not stat.S_ISREG(initial.st_mode) or _stamp(pre) != _stamp(initial)', 'not _matches_path(p, pre, stream, initial)')
edit(base/'verify.py', '_stamp(initial) != _stamp(os.fstat(stream.fileno())) or _stamp(initial) != _stamp(p.lstat())', 'not _unchanged(p, pre, stream, initial)')
for name, pre, stream, old in [
    ('safe_input','before','stream','not stat.S_ISREG(initial.st_mode) or _stamp(initial) != _stamp(before)'),
    ('documents','pre','stream','not stat.S_ISREG(initial.st_mode) or _stamp(pre)!=_stamp(initial)'),
    ('data','pre','stream','not stat.S_ISREG(initial.st_mode) or _stamp(pre)!=_stamp(initial)'),
    ('lens','pre','f','_stamp(pre)!=_stamp(initial) or not stat.S_ISREG(initial.st_mode)'),
    ('metadata','pre','f','_stamp(pre)!=_stamp(initial) or not stat.S_ISREG(initial.st_mode)'),
]:
    path=base/(name+'.py')
    edit(path,'_local_path, _stamp','_local_path, _open_read, _matches_path, _unchanged')
    edit(path,'os.open(p, flags)' if name=='safe_input' else 'os.open(p,flags)','_open_read(p)')
    edit(path,old,f'not _matches_path(p, {pre}, {stream}, initial)')
    old_after=f'_stamp(initial) != _stamp(os.fstat({stream}.fileno())) or _stamp(initial) != _stamp(p.lstat())' if name=='safe_input' else f'_stamp(initial)!=_stamp(os.fstat({stream}.fileno())) or _stamp(initial)!=_stamp(p.lstat())'
    edit(path,old_after,f'not _unchanged(p, {pre}, {stream}, initial)')
# Timer resolution is finite on Windows; preserve validation of invalid samples.
path=root/'desktop/tests/test_health.py'
edit(path,'import sys\n','import sys\nimport time\n')
edit(path,'first=sample(); second=sample(); result=measure(first,second,resident_memory())','first=sample(); time.sleep(0.02); second=sample(); result=measure(first,second,resident_memory())')
path=root/'desktop/tests/test_verify.py'
edit(path,'    def test_migration(self):','''    def test_replacement_at_open_boundary(self):
        from aeris.verify import _open_read, _matches_path
        with TemporaryDirectory() as d:
            p=Path(d)/'original'; replacement=Path(d)/'replacement'
            p.write_bytes(b'abc'); replacement.write_bytes(b'abc')
            before=p.lstat()
            with os.fdopen(_open_read(p),'rb') as f:
                initial=os.fstat(f.fileno())
                self.assertTrue(_matches_path(p,before,f,initial))
                os.replace(replacement,p)
                self.assertFalse(_matches_path(p,before,f,initial))

    def test_migration(self):''')
print('Applied Windows compatibility patch to',root)
