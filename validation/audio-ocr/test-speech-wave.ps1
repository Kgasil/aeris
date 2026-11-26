# Isolated CI only. Synthesize a fictitious sentence to WAV, not to speakers.
# Does not access microphone, user audio, external services, or Windows settings.
param([Parameter(Mandatory)][string]$EvidenceDirectory)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') { throw 'Disposable Windows CI required' }
Add-Type -AssemblyName System.Speech
$dir = (Resolve-Path -LiteralPath $EvidenceDirectory).Path
$wav = Join-Path $dir 'synthetic-speech.wav'
if (Test-Path -LiteralPath $wav) { throw 'Expected fresh output' }
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voices = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled })
    if ($voices.Count -eq 0) { throw 'No enabled desktop voice' }
    $voice = $voices | Where-Object { $_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq 'en' } | Select-Object -First 1
    if (-not $voice) { throw 'No English desktop voice for English fixture' }
    $synth.SelectVoice($voice.VoiceInfo.Name)
    $synth.Rate = 0
    $synth.Volume = 80
    $synth.SetOutputToWaveFile($wav)
    $synth.Speak('Aeris synthetic speech test. No personal information.')
    $synth.SetOutputToNull()
    $selected = $synth.Voice.Culture.Name
    $available = @($voices | ForEach-Object { $_.VoiceInfo.Culture.Name } | Sort-Object -Unique)
} finally { $synth.Dispose() }
$bytes = [IO.File]::ReadAllBytes($wav)
if ($bytes.Length -le 44 -or [Text.Encoding]::ASCII.GetString($bytes,0,4) -ne 'RIFF' -or [Text.Encoding]::ASCII.GetString($bytes,8,4) -ne 'WAVE') { throw 'Invalid WAV output' }
# Evidence contains only a synthetic waveform and technical metadata.
[pscustomobject]@{
    scope='Native System.Speech synthesis to WAV; not playback or microphone; separate from Aeris default-device path'
    synthesis='PASS'
    voice_culture=$selected
    available_cultures=$available
    wav_bytes=$bytes.Length
    wav_sha256=(Get-FileHash -LiteralPath $wav -Algorithm SHA256).Hash.ToLowerInvariant()
    playback='NOT_TESTED'
    microphone='NOT_TESTED'
    release_approved=$false
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dir 'speech-wave.json') -Encoding utf8
