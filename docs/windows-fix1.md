# Windows CI compatibility fix 1

Initial run: https://github.com/Kgasil/aeris/actions/runs/45727874324

The source passed SHA-256 verification and Python x64 setup. The native tests failed before packaging. CPython Windows path and descriptor stat metadata are not interchangeable. The correction preserves bounded reads, native handle identities, reparse checks, and pre/post metadata verification; it does not claim a race-proof OS sandbox. Health's real-sample test now allows time to advance.

Linux validation: 399 unit tests run, 393 passed, 6 skipped; 60 graphical scripts passed. Windows revalidation required.
