"""Bounded feedback from the local Windows recognizer; no audio files."""
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
from aeris.safe_input import strict_json
from aeris.companion import validate_message

LISTEN_SCRIPT=r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
function Emit($kind,$value) {
    [Console]::Out.WriteLine((@{kind=$kind;value=$value}|ConvertTo-Json -Compress))
    [Console]::Out.Flush()
}
$r=$null
try {
    Add-Type -AssemblyName System.Speech
    $info=[System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object {$_.Culture.Name -eq 'pt-BR'} | Select-Object -First 1
    if (-not $info) { Emit 'error' 'recognizer'; exit 2 }
    $r=New-Object System.Speech.Recognition.SpeechRecognitionEngine($info)
    $r.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
    try { $r.SetInputToDefaultAudioDevice() } catch { Emit 'error' 'device'; exit 3 }
    $r.InitialSilenceTimeout=[TimeSpan]::FromSeconds(12)
    $r.EndSilenceTimeout=[TimeSpan]::FromSeconds(1.3)
    Register-ObjectEvent -InputObject $r -EventName AudioLevelUpdated -SourceIdentifier AerisLevel | Out-Null
    Register-ObjectEvent -InputObject $r -EventName AudioStateChanged -SourceIdentifier AerisState | Out-Null
    Register-ObjectEvent -InputObject $r -EventName SpeechHypothesized -SourceIdentifier AerisPartial | Out-Null
    Register-ObjectEvent -InputObject $r -EventName RecognizeCompleted -SourceIdentifier AerisDone | Out-Null
    $r.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Single)
    $watch=[Diagnostics.Stopwatch]::StartNew()
    while ($watch.Elapsed.TotalSeconds -lt 26) {
        $level=$null
        foreach ($event in @(Get-Event | Where-Object {$_.SourceIdentifier -like 'Aeris*'})) {
            $args2=$event.SourceEventArgs
            Remove-Event -EventIdentifier $event.EventIdentifier
            switch ($event.SourceIdentifier) {
                'AerisLevel' { $level=[int]$args2.AudioLevel }
                'AerisState' { Emit 'state' ([string]$args2.AudioState) }
                'AerisPartial' {
                    $text=[string]$args2.Result.Text
                    if ($text.Length -gt 0 -and $text.Length -le 4000) { Emit 'partial' $text }
                }
                'AerisDone' {
                    if ($args2.Error) { Emit 'error' 'recognition'; exit 4 }
                    if ($args2.Cancelled -or -not $args2.Result) { Emit 'error' 'silence'; exit 5 }
                    Emit 'final' ([string]$args2.Result.Text); exit 0
                }
            }
        }
        if ($null -ne $level) { Emit 'level' $level }
        Start-Sleep -Milliseconds 100
    }
    Emit 'error' 'timeout'; exit 6
} catch { Emit 'error' 'recognition'; exit 7 }
finally {
    foreach ($name in @('AerisLevel','AerisState','AerisPartial','AerisDone')) {
        Unregister-Event -SourceIdentifier $name -ErrorAction SilentlyContinue
        Remove-Event -SourceIdentifier $name -ErrorAction SilentlyContinue
    }
    if ($r) { try { $r.RecognizeAsyncCancel() } catch {}; $r.Dispose() }
}
'''
ERRORS={
    'recognizer':'Reconhecedor pt-BR não instalado. Confira os recursos de fala do Windows.',
    'device':'Não foi possível abrir o microfone padrão. Confira o dispositivo e as permissões do Windows.',
    'silence':'Nenhuma fala reconhecida. Confira o nível de entrada ou tente novamente.',
    'timeout':'Tempo de escuta encerrado. Inicie outra pergunta.',
    'recognition':'Falha no reconhecimento local. Confira os recursos de fala do Windows.',
}


def parse_event(raw):
    event=strict_json(raw,8192)
    if not isinstance(event,dict) or set(event)!={'kind','value'}: raise ValueError('Evento de voz inválido.')
    kind,value=event['kind'],event['value']
    if kind=='level' and type(value) is int and 0<=value<=100: return kind,value
    if kind=='state' and value in ('Silence','Speech','Stopped'): return kind,value
    if kind in ('partial','final'): return kind,validate_message(value)
    if kind=='error' and isinstance(value,str) and value in ERRORS: return kind,value
    raise ValueError('Evento de voz inválido.')


def feedback_process():
    if os.name!='nt': raise OSError('Reconhecimento de voz disponível somente no Windows.')
    exe=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
    return subprocess.Popen([str(exe),'-NoLogo','-NoProfile','-NonInteractive','-Command',LISTEN_SCRIPT],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
        encoding='utf-8',errors='strict',creationflags=subprocess.CREATE_NO_WINDOW)


def listen_with_feedback(process,publish):
    events=queue.Queue(maxsize=512)
    overflow=threading.Event()
    def reader():
        try:
            for _ in range(512):
                raw=process.stdout.readline(8193)
                if not raw: break
                events.put_nowait(parse_event(raw))
            else: overflow.set()
        except Exception: overflow.set()
        finally:
            try: events.put_nowait(('end',None))
            except queue.Full: overflow.set()
    thread=threading.Thread(target=reader,daemon=True); thread.start()
    deadline=time.monotonic()+36
    final=None; error='recognition'
    try:
        while time.monotonic()<deadline:
            if overflow.is_set(): break
            try: kind,value=events.get(timeout=.2)
            except queue.Empty: continue
            if kind=='end':
                if final is not None and process.wait(timeout=3)==0: return ('ok',final)
                return ('error',error)
            if kind=='error': error=value
            elif kind=='final': final=value
            else: publish((kind,value))
        return ('error','timeout' if time.monotonic()>=deadline else error)
    finally:
        if process.poll() is None:
            process.kill()
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired: pass
        thread.join(timeout=1)
        if not thread.is_alive(): process.stdout.close()
