"""Native Windows source-level regression tests using only synthetic temporary data."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from aeris.dpapi import WindowsDPAPI
from aeris.vault import Vault, MAGIC
from aeris.distribution import application_lock

def run_child(code, *args):
    return subprocess.run([sys.executable, "-c", code, *map(str, args)],
                          capture_output=True, text=True, timeout=20, check=True)

@unittest.skipUnless(sys.platform == "win32", "Native Windows required")
class NativeSecurity(unittest.TestCase):
    def test_dpapi_across_processes_same_account(self):
        payload = b"Aeris native synthetic security fixture " + os.urandom(32)
        with tempfile.TemporaryDirectory(prefix="aeris-native-") as tmp:
            file = Path(tmp) / "fixture.bin"
            blob = WindowsDPAPI().protect(payload)
            self.assertNotIn(payload, blob)
            file.write_bytes(blob)
            result = run_child("from aeris.dpapi import WindowsDPAPI; from pathlib import Path; import hashlib,sys; print(hashlib.sha256(WindowsDPAPI().unprotect(Path(sys.argv[1]).read_bytes())).hexdigest())", file)
            self.assertEqual(result.stdout.strip(), hashlib.sha256(payload).hexdigest())

    def test_dpapi_tamper_and_invalid_input(self):
        api = WindowsDPAPI()
        with self.assertRaises(ValueError):
            api.protect(b"")
        with self.assertRaises(OSError):
            api.unprotect(b"invalid synthetic blob")
        blob = bytearray(api.protect(b"synthetic fixture"))
        # Corrupt the entire encrypted tail, not just an optional header field.
        blob[len(blob)//2:] = b"\0" * (len(blob) - len(blob)//2)
        with self.assertRaises(OSError):
            api.unprotect(bytes(blob))

    def test_vault_native_roundtrip_and_failed_unlock_preserves_ciphertext(self):
        with tempfile.TemporaryDirectory(prefix="aeris-vault-") as tmp:
            path = Path(tmp) / "vault.bin"
            token = "AERIS-SYNTHETIC-" + uuid.uuid4().hex
            v = Vault(path)
            try:
                v.unlock()
                item = v.save("Synthetic entry", token)
                raw = path.read_bytes()
                self.assertTrue(raw.startswith(MAGIC))
                self.assertNotIn(token.encode(), raw)
                self.assertNotIn(token.encode("utf-16-le"), raw)
                v.lock()
                v.unlock()
                self.assertEqual(v.list(), (item,))
                v.lock()
                damaged = MAGIC + b"invalid ciphertext"
                path.write_bytes(damaged)
                with self.assertRaises((OSError, ValueError)):
                    v.unlock()
                self.assertFalse(v.unlocked)
                self.assertEqual(path.read_bytes(), damaged)
                path.write_bytes(raw)
                v.unlock()
                self.assertEqual(v.list(), (item,))
            finally:
                v.lock()

    def test_native_mutex_cross_process_and_abrupt_exit(self):
        name = r"Local\KGVision.Aeris.Test." + str(uuid.uuid4())
        child = (
            "import os,sys,time; import aeris.distribution as d; "
            "sys.frozen=True; d.APP_MUTEX=sys.argv[1]; "
            "lock=d.application_lock(); assert lock.__enter__(); "
            "print('READY:'+str(os.getpid()),flush=True); time.sleep(60)"
        )
        with tempfile.TemporaryDirectory(prefix="aeris-mutex-") as tmp:
            ready = Path(tmp) / "ready.txt"
            # Redirect readiness to a file to enforce a bounded wait.
            import time
            with ready.open("w", encoding="utf-8") as output:
                # On Windows a venv executable may be a redirector with a different PID.
                # Terminate the actual holder, not a launcher that could leave it alive.
                interpreter = Path(getattr(sys, "_base_executable", sys.executable))
                self.assertTrue(interpreter.is_file())
                p = subprocess.Popen([str(interpreter), "-c", child, name],
                                     stdout=output, stderr=subprocess.DEVNULL)
                try:
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        if p.poll() is not None:
                            self.fail("Mutex holder exited early")
                        if ready.read_text(encoding="utf-8").strip() == f"READY:{p.pid}":
                            break
                        time.sleep(0.1)
                    else:
                        self.fail("Mutex holder did not become ready")
                    with patch.object(sys, "frozen", True, create=True), patch("aeris.distribution.APP_MUTEX", name):
                        with application_lock() as acquired:
                            self.assertFalse(acquired)
                        # Kill only this synthetic test child, not any user application.
                        p.terminate()
                        p.wait(timeout=15)
                        with application_lock() as acquired:
                            self.assertTrue(acquired)
                finally:
                    if p.poll() is None:
                        p.kill()
                        p.wait(timeout=15)

    def test_vault_native_lock_across_process(self):
        with tempfile.TemporaryDirectory(prefix="aeris-vault-lock-") as tmp:
            path = Path(tmp) / "vault.bin"
            v = Vault(path)
            code = (
                "import sys; from aeris.vault import Vault; v=Vault(sys.argv[1]); "
                "\ntry: v.unlock()\nexcept OSError: print('BLOCKED')"
                "\nelse: v.lock(); print('ACQUIRED')"
            )
            try:
                v.unlock()
                v.save("Synthetic", "Synthetic body")
                before = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(run_child(code, path).stdout.strip(), "BLOCKED")
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
                v.lock()
                self.assertEqual(run_child(code, path).stdout.strip(), "ACQUIRED")
            finally:
                v.lock()

if __name__ == "__main__":
    if sys.platform != "win32":
        raise SystemExit("Native Windows required; no simulated pass")
    unittest.main(verbosity=2)
