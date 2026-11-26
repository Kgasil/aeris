"""Consent-based Windows AI setup. No shell, cloud, public listener or device access.

Downloads use Windows Package Manager's official manifest/hash validation and
Ollama's own model registry. A private model store and a separate loopback
listener avoid changing or stopping another Ollama installation.
"""
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import time

from aeris.safe_input import bounded_read, strict_json

MODELS = {'qwen2.5:1.5b': 3, 'qwen2.5vl:3b': 6}  # minimum free GiB for model store
DEFAULT_PORT = 11434
MANAGED_PORT = 11435
_port = DEFAULT_PORT


def local_port():
    return _port


def select_managed():
    global _port
    _port = MANAGED_PORT


def reset_endpoint():
    global _port
    _port = DEFAULT_PORT


def load_choice(path):
    try:
        data = strict_json(bounded_read(Path(path), 1024), 1024)
        model = data.get('model') if isinstance(data, dict) else None
        return model if isinstance(model, str) and model in MODELS else None
    except (OSError, ValueError, TypeError):
        return None


def save_choice(path, model):
    if model not in MODELS:
        raise ValueError('Modelo não permitido.')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
            tmp = Path(f.name)
            json.dump({'model': model}, f)
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def check_cancel(cancel):
    if cancel.is_set():
        raise InterruptedError('Configuração cancelada. Você pode tentar novamente.')


def wait_command(argv, env, cancel, seconds):
    check_cancel(cancel)
    p = subprocess.Popen([str(a) for a in argv], env=env, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    deadline = time.monotonic() + seconds
    try:
        while p.poll() is None:
            check_cancel(cancel)
            if time.monotonic() >= deadline:
                raise TimeoutError('Tempo limite da instalação ou download atingido.')
            cancel.wait(.25)
        if p.returncode != 0:
            raise OSError('O instalador ou download retornou erro. Confira a conexão e os alertas do Windows.')
    finally:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=5)


def installed_executable(local_appdata):
    # Do not launch an arbitrary PATH executable or download a script.
    exe = Path(local_appdata) / 'Programs' / 'Ollama' / 'ollama.exe'
    return exe if exe.is_file() else None


def runtime_env(model_dir):
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith('OLLAMA_')}
    env.update(OLLAMA_NO_CLOUD='1', OLLAMA_HOST='127.0.0.1:11435',
               OLLAMA_MODELS=str(model_dir), OLLAMA_NUM_PARALLEL='1',
               OLLAMA_MAX_LOADED_MODELS='1')
    return env


class ManagedRuntime:
    def __init__(self, settings_path):
        self.root = Path(settings_path).parent / 'local-ai'
        self.choice = self.root / 'choice.json'
        self.models = self.root / 'models'
        self.process = None
        self.lock = threading.Lock()

    def _available_port(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', MANAGED_PORT))

    def _ready(self):
        conn = http.client.HTTPConnection('127.0.0.1', MANAGED_PORT, timeout=2)
        try:
            conn.request('GET','/api/version')
            reply = conn.getresponse()
            obj = strict_json(reply.read(1025),1024)
            return reply.status == 200 and isinstance(obj,dict) and isinstance(obj.get('version'),str)
        except (OSError, ValueError, http.client.HTTPException):
            return False
        finally:
            conn.close()

    def close(self):
        with self.lock:
            p, self.process = self.process, None
            if p is not None and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=3)

    def prepare(self, model, cancel, progress, *, download):
        if os.name != 'nt':
            raise OSError('A configuração integrada está disponível no Windows.')
        if model not in MODELS:
            raise ValueError('Modelo não permitido.')
        local = os.environ.get('LOCALAPPDATA')
        if not local:
            raise OSError('Pasta local do Windows indisponível.')
        check_cancel(cancel)
        self.models.mkdir(parents=True, exist_ok=True)
        env = runtime_env(self.models)
        exe = installed_executable(local)
        if download and shutil.disk_usage(self.models).free < MODELS[model]*1024**3:
            raise OSError('Espaço insuficiente. Libere espaço ou escolha o modo leve.')
        if exe is None:
            if not download:
                raise OSError('Ollama não encontrado. Clique Preparar IA para reinstalar.')
            winget = Path(local)/'Microsoft'/'WindowsApps'/'winget.exe'
            if not winget.is_file():
                raise OSError('Windows Package Manager indisponível. Abra a fonte oficial do Ollama ou instale o App Installer pela Microsoft Store.')
            progress('Instalando Ollama pela fonte oficial do WinGet…')
            wait_command([winget,'install','--id','Ollama.Ollama','--exact','--source','winget',
                          '--scope','user','--silent','--disable-interactivity',
                          '--accept-source-agreements','--accept-package-agreements'],
                         env,cancel,1800)
            exe = installed_executable(local)
            if exe is None:
                raise OSError('Instalação não localizada. Confira o Ollama e tente novamente.')
        check_cancel(cancel)
        select_managed()  # Fail closed on the managed endpoint, never fall back to the other server.
        try:
            progress('Iniciando IA local (sem nuvem)…')
            with self.lock:
                check_cancel(cancel)
                if self.process is None or self.process.poll() is not None:
                    self._available_port()  # Never reuse a listener owned by another process.
                    self.process = subprocess.Popen([str(exe),'serve'],env=env,
                        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                p = self.process
            deadline = time.monotonic()+45
            while not self._ready():
                check_cancel(cancel)
                if p.poll() is not None or time.monotonic() >= deadline:
                    raise OSError('O servidor local não iniciou. Confira o Ollama e tente novamente.')
                cancel.wait(.5)
            if p.poll() is not None:
                raise OSError('O servidor local terminou inesperadamente.')
            from aeris.screen_context import installed_models
            if model not in installed_models():
                if not download:
                    raise OSError('Modelo ausente. Clique Preparar IA para baixá-lo.')
                progress('Baixando modelo local. Esta etapa pode demorar; não feche o Aeris…')
                wait_command([exe,'pull',model],env,cancel,7200)
            check_cancel(cancel)
            if model not in installed_models() or p.poll() is not None:
                raise OSError('O modelo local não foi confirmado.')
            if download:
                progress('Testando a IA com uma mensagem fictícia…')
                from aeris.ready import check_model
                from aeris.companion import chat
                check_model(model,chat_fn=chat)
                check_cancel(cancel)
                save_choice(self.choice,model)
            return model
        except BaseException:
            self.close()
            raise
