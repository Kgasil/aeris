"""Windows desktop speech synthesis; fixed PowerShell program, data via stdin only."""
import json
import os
from pathlib import Path
import subprocess

MAX_TEXT = 4000
# No shell interpolation, files, SSML, microphone or online service calls.
SCRIPT = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $p = [Console]::In.ReadToEnd() | ConvertFrom-Json
    if ($p.action -eq 'list') {
        $voices = @($s.GetInstalledVoices() | Where-Object { $_.Enabled -and (-not $p.language -or $_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq [string]$p.language) } | ForEach-Object { $_.VoiceInfo.Name })
        ConvertTo-Json -InputObject $voices -Compress
    } elseif ($p.action -eq 'speak') {
        if ($p.voice) { $s.SelectVoice([string]$p.voice) }
        $s.Rate = [int]$p.rate
        $s.Volume = [int]$p.volume
        $s.SetOutputToDefaultAudioDevice()
        $count = 1
        if ($p.repeat) { $count = [int]$p.repeat }
        if ($count -lt 1 -or $count -gt 5) { throw 'Invalid repeat' }
        if ($p.language -and $s.Voice.Culture.TwoLetterISOLanguageName -ne [string]$p.language) { throw 'Voice language mismatch' }
        for ($i = 0; $i -lt $count; $i++) {
            if ($i -gt 0) { Start-Sleep -Milliseconds 700 }
            $s.Speak([string]$p.text)
        }
    } else { throw 'Invalid action' }
} finally { $s.Dispose() }
'''

def speech_payload(text, voice='', rate=0, volume=80):
    if not isinstance(text,str) or not text.strip() or len(text)>MAX_TEXT or '\0' in text:
        raise ValueError('Digite de 1 a 4.000 caracteres válidos.')
    if not isinstance(voice,str) or len(voice)>256 or '\0' in voice:
        raise ValueError('Voz inválida.')
    if type(rate) is not int or not -5<=rate<=5 or type(volume) is not int or not 0<=volume<=100:
        raise ValueError('Velocidade ou volume inválido.')
    return dict(action='speak',text=text,voice=voice,rate=rate,volume=volume)

def parse_voices(raw):
    data=json.loads(raw)
    if not isinstance(data,list) or any(not isinstance(v,str) or not v or len(v)>256 for v in data):
        raise ValueError('Lista de vozes inválida.')
    return tuple(dict.fromkeys(data))

def start_process():
    if os.name!='nt': raise OSError('Síntese nativa disponível somente no Windows.')
    root=Path(os.environ.get('SystemRoot',r'C:\Windows'))
    executable=root/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
    return subprocess.Popen([str(executable),'-NoLogo','-NoProfile','-NonInteractive','-Command',SCRIPT],
                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                            encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)

def serialize(payload):
    # ASCII JSON escapes Unicode, avoiding PowerShell console input codepage differences.
    return json.dumps(payload,ensure_ascii=True)
