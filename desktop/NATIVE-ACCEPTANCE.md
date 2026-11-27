# Aeris — Native acceptance / Aceitação nativa
Status: **NOT EXECUTED / NÃO EXECUTADO**. Release hold; minimum measured 9/10 plus all mandatory gates. No release authorization.

## Environment and evidence
Use two authorized disposable clean Windows client VMs (Windows 10 and 11, record edition/build and support status), with physical mic/audio and local model on an authorized client where necessary. Do not weaken Defender or change exclusions. Use fictitious data, no customer records, no unconsented meeting capture. Record exact commit, installer and portable SHA-256, OS, CPU/RAM, model/version, microphone/device, display scaling, UTC, tester. Build from exact reviewed commit or receive the same candidate through an authorized private handoff; compare actual bytes with the build manifest before testing. Evidence-only CI ZIP does not contain the binaries. No public distribution.

## Matrix (each OS, unless noted)
| ID | Scenario | Required observable result |
|---|---|---|
| N01 | Hash both packages, verify Authenticode, inspect active AV and fresh definitions | Exact hashes match; unsigned status disclosed; complete scan evidence for exact targets; no skipped scans counted as pass |
| N02 | Decline terms, install, launch, self-test, same-version reinstall and uninstall; test supported prior-version upgrade separately | Refusal makes no installation; successful install; manifest matches; only synthetic data preserved; upgrade documented |
| N03 | Local AI setup with supported model, send synthetic question, unavailable model, cancel/restart | Real answer, actionable failure, cancellation; record startup/first-token/full latency and memory |
| N04 | pt-BR physical microphone, playback, denial, stop and revoke | Recognizes known phrase, audible speech, indicators accurate, no late result after revoke |
| N05 | Screen capture synthetic document, deny/allow, explicit send to compatible vision model, discard | Correct contextual answer; no unsolicited capture/send; revoke stops processing |
| N06 | Consenting or synthetic meeting, record mic, transcribe, edit notes and review minutes before saving; delete | Transcription and manual notes separated; reviewed output only; deletion works; optional system audio availability accurately communicated |
| N07 | 50 tools, primary task, invalid input, close/reopen and permissions | Record 50 individual results per OS; no lost user input or retained windows |
| N08 | Dark/light, keyboard, 100/125/150% DPI, native icon and scrollbar, 980x660 compact layout | All controls reachable; focus visible, no clipping; logo and green identity retained |
| N09 | Repeated open/close and AI cancellation cycles, DPAPI/mutex and safe restart | Record memory/CPU and time; no stale activity, unauthorized data or corruption |

Record one result per scenario and OS: PASS / FAIL / BLOCKED / NOT RUN, observed result, exact evidence reference, severity, reproduction steps, measurement units. Screenshots must contain synthetic data only. A mock or Windows Server run cannot substitute for physical/native client acceptance. Resolve critical/high issues; retain measured scoring rubric in FINAL-UX-AUDIT.md. Do not assign a score to unmeasured categories. 
