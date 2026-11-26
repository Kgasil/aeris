"""On-demand current-process measurements. No process enumeration or telemetry."""
from dataclasses import dataclass
import math
import os
import sys
import time


def windows_memory():
    """Current resident working set (bytes), not private bytes or peak usage."""
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
                'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    current = kernel.GetCurrentProcess
    current.argtypes = []; current.restype = wintypes.HANDLE
    get = psapi.GetProcessMemoryInfo
    get.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    get.restype = wintypes.BOOL
    data = Counters(); data.cb = ctypes.sizeof(data)
    if not get(current(), ctypes.byref(data), data.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(data.WorkingSetSize)


def resident_memory():
    """Return current resident memory or None when unsupported/unavailable."""
    try:
        if sys.platform == 'win32': return windows_memory()
        if sys.platform.startswith('linux'):
            with open('/proc/self/statm', 'r', encoding='ascii') as f:
                return int(f.read(256).split()[1]) * os.sysconf('SC_PAGE_SIZE')
    except (OSError, ValueError, IndexError, AttributeError):
        pass
    return None


@dataclass(frozen=True)
class Sample:
    wall: float
    cpu: float


@dataclass(frozen=True)
class Measurement:
    seconds: float
    cpu_percent: float
    resident_bytes: int | None


def sample():
    return Sample(time.monotonic(), time.process_time())


def measure(start, end, memory):
    elapsed = end.wall - start.wall
    cpu = end.cpu - start.cpu
    if not math.isfinite(elapsed) or not math.isfinite(cpu) or elapsed <= 0 or cpu < 0:
        raise ValueError('Amostra inválida.')
    if memory is not None and (type(memory) is not int or memory < 0):
        raise ValueError('Memória inválida.')
    # 100% = one logical CPU, can exceed 100% for a multithreaded process.
    return Measurement(elapsed, 100 * (cpu / elapsed), memory)
