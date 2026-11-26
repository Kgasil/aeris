"""Optional local conversation and explicit Windows speech. No model-driven execution."""
import http.client
import json
import re
import os
import subprocess
from pathlib import Path
from aeris.safe_input import strict_json

MAX_MESSAGE=4000
MAX_HISTORY=12
MAX_RESPONSE=256*1024
SYSTEM='Você é Aeris, um assistente de IA profissional e amigável. Responda em português quando apropriado. Não simule vínculo romântico ou dependência. Não afirme ter executado ações, acessado arquivos ou ter memória fora desta conversa. Não possui ferramentas. Para ações, oriente o usuário a revisar o comando no Copilot.'

def validate_message(text):
    if not isinstance(text,str) or not text.strip() or len(text)>MAX_MESSAGE or '\0' in text:
        raise ValueError('Digite de 1 a 4.000 caracteres válidos.')
    return text.strip()

def chat(model, history, text, *, connection_factory=http.client.HTTPConnection, system=SYSTEM):
    if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}',model) or 'cloud' in model.lower():
        raise ValueError('Informe o nome de um modelo instalado localmente, sem cloud.')
    if len(history)>MAX_HISTORY or len(history)%2: raise ValueError('Histórico inválido.')
    messages=[{'role':'system','content':system}]
    for i,(role,content) in enumerate(history):
        if role!=('user' if i%2==0 else 'assistant'): raise ValueError('Histórico inválido.')
        messages.append({'role':role,'content':validate_message(content)})
    messages.append({'role':'user','content':validate_message(text)})
    body=json.dumps(dict(model=model,messages=messages,stream=False,keep_alive=0,options={'num_predict':512,'num_ctx':4096}),ensure_ascii=True).encode()
    # Fixed loopback endpoint, no proxies, redirects, custom host or tool calls.
    conn=connection_factory('127.0.0.1',11434,timeout=45)
    try:
        conn.request('POST','/api/chat',body,{'Content-Type':'application/json'})
        response=conn.getresponse()
        if response.status!=200: raise OSError('Servidor local não respondeu com sucesso. Confira o modelo instalado.')
        raw=response.read(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE: raise ValueError('Resposta acima do limite.')
        obj=strict_json(raw, MAX_RESPONSE)
        if not isinstance(obj,dict) or obj.get('done') is not True or obj.get('error'): raise ValueError('Resposta incompleta ou inválida.')
        msg=obj.get('message')
        if not isinstance(msg,dict) or msg.get('role')!='assistant' or msg.get('tool_calls'): raise ValueError('Resposta inválida ou operação não autorizada.')
        return validate_message(msg.get('content'))
    finally: conn.close()

COMMAND_SYSTEM = ("Converta somente a solicitação explícita em português em UM comando do Aeris. "
    "Não invente informações ou escolha ações que não foram pedidas. Se faltar dado, responda INSUFICIENTE. "
    "Formatos permitidos: Lembre-me de TÍTULO em N minutos; Marque TÍTULO hoje ou amanhã às HH:MM; "
    "Adicione TAREFA à lista NOME; Inicie uma concentração de N minutos; Anote minha ideia de TÍTULO. "
    "Retorne apenas o comando, sem aspas, explicações ou Markdown. Não execute nada.")


def suggest_command(model, text, *, connection_factory=http.client.HTTPConnection):
    """A suggestion only; no history, tool execution, or access to other records."""
    from aeris.copilot import parse_command
    original = validate_message(text)
    if len(original) > 500:
        raise ValueError('Solicitação de ação: até 500 caracteres.')
    candidate = chat(model, (), original, connection_factory=connection_factory, system=COMMAND_SYSTEM)
    if candidate == 'INSUFICIENTE':
        raise ValueError('Faltam dados para preparar um comando.')
    parse_command(candidate)  # Whitelist syntax, bounds and local dates; no mutation.
    return candidate


SPEECH_SCRIPT=r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Speech
$p=[Console]::In.ReadToEnd() | ConvertFrom-Json
if ($p.action -eq 'listen') {
    $info=[System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object { $_.Culture.Name -eq 'pt-BR' } | Select-Object -First 1
    if (-not $info) { throw 'No pt-BR recognizer' }
    $r=New-Object System.Speech.Recognition.SpeechRecognitionEngine($info)
    try {
        $r.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
        $r.SetInputToDefaultAudioDevice()
        $r.InitialSilenceTimeout=[TimeSpan]::FromSeconds(8)
        $r.EndSilenceTimeout=[TimeSpan]::FromSeconds(1)
        $result=$r.Recognize([TimeSpan]::FromSeconds(8))
        if ($null -eq $result) { throw 'No speech' }
        ConvertTo-Json -InputObject ([string]$result.Text) -Compress
    } finally { $r.Dispose() }
} elseif ($p.action -eq 'speak') {
    $s=New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $v=$s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Gender -eq 'Male' -and $_.VoiceInfo.Culture.Name -eq 'pt-BR' } | Select-Object -First 1
        if (-not $v) { throw 'No male pt-BR voice' }
        $s.SelectVoice($v.VoiceInfo.Name); $s.Rate=0; $s.Volume=80
        $s.SetOutputToDefaultAudioDevice(); $s.Speak([string]$p.text)
    } finally { $s.Dispose() }
} else { throw 'Invalid action' }
'''

def speech_process():
    if os.name!='nt': raise OSError('Voz disponível somente no Windows.')
    exe=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
    return subprocess.Popen([str(exe),'-NoLogo','-NoProfile','-NonInteractive','-Command',SPEECH_SCRIPT],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
