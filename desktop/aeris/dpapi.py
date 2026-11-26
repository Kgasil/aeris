"""Windows DPAPI, escopo do usuário atual. Não há fallback de criptografia."""
import ctypes as c
from ctypes import wintypes as w
import sys

class DataBlob(c.Structure):
    _fields_ = [('cbData', w.DWORD), ('pbData', c.POINTER(c.c_ubyte))]

class WindowsDPAPI:
    def __init__(self):
        if sys.platform != 'win32':
            raise OSError('Vault requer Windows com DPAPI.')
        self.api = c.WinDLL('crypt32', use_last_error=True)
        self.kernel = c.WinDLL('kernel32', use_last_error=True)
        self.kernel.LocalFree.argtypes = [c.c_void_p]
        self.kernel.LocalFree.restype = c.c_void_p
        common = [c.POINTER(DataBlob), c.c_void_p, c.POINTER(DataBlob), c.c_void_p, c.c_void_p, w.DWORD, c.POINTER(DataBlob)]
        for fn in (self.api.CryptProtectData, self.api.CryptUnprotectData):
            fn.argtypes = common
            fn.restype = w.BOOL

    def _run(self, fn, data):
        if not data or len(data) > 32*1024*1024:
            raise ValueError('Tamanho inválido para DPAPI.')
        buf = (c.c_ubyte * len(data)).from_buffer_copy(data)
        src = DataBlob(len(data), buf)
        dst = DataBlob()
        try:
            # UI_FORBIDDEN, sem LOCAL_MACHINE. Sem prompt obsoleto.
            if not fn(c.byref(src), None, None, None, None, 1, c.byref(dst)):
                raise c.WinError(c.get_last_error())
            return c.string_at(dst.pbData, dst.cbData)
        finally:
            c.memset(buf, 0, len(data))
            if dst.pbData:
                c.memset(dst.pbData, 0, dst.cbData)
                self.kernel.LocalFree(c.cast(dst.pbData, c.c_void_p))

    def protect(self, data): return self._run(self.api.CryptProtectData, data)
    def unprotect(self, data): return self._run(self.api.CryptUnprotectData, data)
