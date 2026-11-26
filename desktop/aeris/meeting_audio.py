"""Optional source-mode Windows loopback. No audio files or model downloads."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

BLOCK_SECONDS=30
TIMEOUT_SECONDS=180

def available():
    return sys.platform=='win32' and not getattr(sys,'frozen',False) and all(
        importlib.util.find_spec(name) is not None for name in ('soundcard','faster_whisper','numpy'))

def model_path(value):
    p=Path(value).resolve(strict=True)
    if not p.is_dir() or not all((p/name).is_file() for name in ('model.bin','config.json','tokenizer.json')):
        raise ValueError('Selecione uma pasta local de modelo Whisper convertido, com model.bin, config.json e tokenizer.json.')
    return p

def start_loopback(model):
    if not available():
        raise OSError('Áudio interno experimental disponível somente no Windows por código-fonte com dependências instaladas.')
    p=model_path(model)
    env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',PYTHONIOENCODING='utf-8')
    return subprocess.Popen([sys.executable,'-m','aeris.meeting_audio',str(p)],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,encoding='utf-8',env=env,cwd=str(Path(__file__).resolve().parent.parent),creationflags=subprocess.CREATE_NO_WINDOW)

def read_loopback(process):
    from aeris.safe_input import strict_json
    try:
        output,_=process.communicate(timeout=TIMEOUT_SECONDS)
        if process.returncode: raise OSError('Captura ou transcrição de áudio interno indisponível.')
        text=strict_json(output,32768)
        if not isinstance(text,str) or len(text)>4000 or '\0' in text: raise ValueError('Transcrição inválida.')
        return text.strip()
    except subprocess.TimeoutExpired:
        process.kill(); process.communicate()
        raise OSError('Tempo limite do áudio interno atingido.')

def transcribe(model):
    import soundcard as sc
    import numpy as np
    from faster_whisper import WhisperModel
    engine=WhisperModel(str(model_path(model)),device='cpu',compute_type='int8',local_files_only=True)
    speaker=sc.default_speaker()
    loop=sc.get_microphone(id=speaker.id,include_loopback=True)
    if not loop.isloopback: raise OSError('Dispositivo não é loopback.')
    with loop.recorder(samplerate=48000) as recorder:
        audio=recorder.record(numframes=48000*BLOCK_SECONDS)
    mono=np.asarray(audio,dtype=np.float32).mean(axis=1)
    mono=mono[:len(mono)//3*3].reshape(-1,3).mean(axis=1)
    if not len(mono) or not np.isfinite(mono).all(): raise ValueError('Áudio inválido.')
    if float(np.max(np.abs(mono)))<0.001: return ''
    segments,_=engine.transcribe(mono,language='pt',beam_size=1,vad_filter=True,condition_on_previous_text=False)
    return ' '.join(s.text.strip() for s in segments).strip()[:4000]

if __name__=='__main__':
    try:
        if sys.platform!='win32' or len(sys.argv)!=2: raise ValueError('Invocação inválida.')
        print(json.dumps(transcribe(sys.argv[1]),ensure_ascii=True))
    except Exception:
        sys.exit(1)
