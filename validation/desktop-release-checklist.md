# Aeris Desktop — release checklist / checklist de lançamento

Scope: Desktop 1.0.0rc1, Windows x64. Extension 1.0.0 is a separate distribution. Do not use real personal data in the preview.

## Evidence already recorded

- [Native Windows unit tests and portable build](https://github.com/Kgasil/aeris/actions/runs/45730089078): 395 passed, four skipped; packaged UI self-test; Windows Server 2022.
- [Installer CI](https://github.com/Kgasil/aeris/actions/runs/45730507059): install, same-version reinstall, uninstall and synthetic-data preservation passed.
- [Historical checksums](../downloads/windows-preview-evidence.json). These apply only to the recorded artifact, not subsequent builds.

## Clean Windows 10/11 validation (manual)

Use separate disposable x64 VMs with supported Windows editions/builds, clean snapshots, ordinary user accounts and no preinstalled Python or Aeris. Record OS build, installer SHA-256, timestamp and each result. Do not disable Defender or bypass SmartScreen to make a test pass.

| Check | Pass criterion |
| --- | --- |
| Install from downloaded Setup.exe | User opens file and confirms installation; no Python/terminal/manual dependencies; no unexpected elevation; Start menu entry works |
| First launch | Hub opens and packaged assets load; offline core tools work |
| Reinstall same version | App remains usable and synthetic notes/settings preserved |
| Upgrade from prior version | Install a genuine previous packaged version, create synthetic data, install newer version, verify data and version; if no prior package exists mark not tested |
| Uninstall | App, shortcuts and application files removed; documented user-data behavior observed |
| DPAPI | Protect and unprotect synthetic secret in same Windows account; another account cannot decrypt it; no plaintext at rest |
| Mutex | Launch two instances; confirm duplicate handling and recovery after exit/crash |
| AI | Optional Ollama installed separately with approved model; actual local response, timeout and unavailable-service handling |
| Audio | Explicit consent; test synthetic/consented sample, playback/capture as applicable, permission denial and cleanup |
| OCR | Known synthetic image with text; compare extracted result and handle missing OCR dependency |
| Performance | Record cold launch, idle CPU/RAM, module launch and shutdown on both VMs; define thresholds before final approval |
| Accessibility | Keyboard-only navigation, visible focus, Windows Narrator, high contrast and 100%/150% scaling; log defects |

Record PASS, FAIL or NOT TESTED for each OS and criterion. Capture logs/screenshots without secrets; retain test evidence. A Windows Server CI pass is not a Windows 10/11 pass.

## Licensing and trust (publication gate)

- Inventory bundled Python, Tcl/Tk, PyInstaller bootloader, libraries, fonts, icons, installers and any external assets. Identify exact versions and applicable terms; verify notices and obligations against the actual binary contents.
- Confirm redistribution rights for first-party code and all bundled assets; provide required notices/license texts. Ollama, model weights and optional OCR/audio dependencies must be reviewed separately if distributed.
- Verify SHA-256, malware-scan the actual installer, review SmartScreen behavior and Authenticode signing options. Do not claim a signed or certified build without evidence.
- Record review approval in a public-safe reference; never enter secrets or private notes in workflow inputs.

## Publish the experimental preview (only after review)

Open [Aeris Windows installer preview validation](https://github.com/Kgasil/aeris/actions/workflows/aeris-windows-installer-preview.yml), choose Run workflow on main, enable publish_preview and enter the completed redistribution/trust review reference. CI builds and tests; publication proceeds only after successful validation. The workflow refuses to overwrite an existing preview tag. It creates a separate, explicitly unsigned experimental prerelease with Setup.exe, portable ZIP, SHA-256 and validation evidence. The website detects the expected uploaded Setup.exe asset and displays the direct download; otherwise the test-build link remains.

This does not approve Windows 10/11 compatibility or stable release. Stable 1.0.0 requires closing all release gates, a versioned upgrade test, reviewed distribution notices and verified release assets.
