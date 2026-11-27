# Project Aeris — Block 12 / final audit
Date: 2026-11-27. Scope: desktop-experience only. No public distribution changes.

## Evidence and verdict
**NOT APPROVED FOR RELEASE.** Minimum 9/10 is an acceptance threshold, not an assigned score. A final score requires evidence on the exact release candidate; missing measurements are not passes.

The previous approved Windows and Ubuntu regression jobs and candidate build belong to workflow 46056511397, head 4a2fd1bf538a43e823d59246c604881e893704de. The audited pre-fix head adc8741d48ec83f2dad61441fcc207fcd02050a9 was 15 commits ahead of that baseline, touching 9 files. The available commit-workflow and combined-status queries returned no runs/statuses for adc8741. A direct clone from the local execution environment failed DNS resolution; no new full current-branch test run or screenshot inspection is claimed.

Previous archived RC5 evidence (not current head): 477 tests, 466 passes, 11 skips, 45 windows opened/released, 3 Windows-only modules correctly refused on Linux, Hub and Spotlight checked; 65 lifecycle cycles without retained window objects detected. See Block 11 record.

## Current source checks
- catalog.json: 50 entries, 50 unique IDs and names, 10 categories, all marked prototype; exact coverage by 50 localized names and 50 help entries.
- Settings: Escuro is the default; explicit persisted light choice preserved.
- Official main assets/aeris-symbol.svg geometry matches WIND_CURVES in desktop theme: three identical cubic paths.
- Calculated 25 text/background combinations per palette: 50/50 >=4.5:1. Minimum light 5.4459:1, dark 6.2039:1. Three focus/surface combinations per palette: minimum light 5.4765:1, dark 7.7556:1, all >=3:1. This is a color-token check, not measured WCAG conformance of every rendered widget.
- Consent dialog source retains refusal on close/Escape, explicit approval and initial focus on refusal. Native execution and revocation regressions still required on current head.
- Fixed missing theme-dependent focus outline on marked scrolling canvases (cb05b61); preview contents and unrelated canvases unchanged. Regression added (8ff54d1); not run on current head.

## Review of the 12 blocks
| Block | Evidence | Acceptance |
|---|---|---|
| 01 Shared design | Color tokens and geometry checked | Visual regression pending |
| 02 Main UI | Previous CI | Current DPI/layout checks pending |
| 03 Chat and performance | Previous CI | Actual local-model latency pending |
| 04 AI setup | Previous CI | Windows setup/download/restore pending |
| 05 Permissions | Source and prior CI | Current deny/revoke regression pending |
| 06 Voice | Previous CI | Physical pt-BR recognition and playback pending |
| 07 Screen | Previous CI | Current physical capture/vision model pending |
| 08 Meetings | Previous CI | Native mic, transcription and minutes acceptance pending |
| 09 Tools | 50/50 catalog coverage | Current all-window test and per-tool functional scenarios pending |
| 10 Accessibility | Source and palette checks | Current keyboard, small-window and scaling checks pending |
| 11 Integrated tests | Test code and archived baseline | Current Windows/Linux execution pending |
| 12 Audit | This report and focus correction | Release blocked |

## Acceptance protocol
Use an exact immutable commit SHA. From desktop, run python -m unittest discover -v with real Tk display on Windows and Xvfb on Linux. Record output, skipped tests and platform. Run tests.test_experience, tests.test_polish and tests.test_integrated_windows specifically, and existing candidate build/self-tests; review every failure and skip. Test 50 entries with fictitious inputs; record launch, primary task, expected output, invalid input, cleanup and consent (where relevant), in dark/light at supported window sizes and Windows scaling 100/125/150%. Check keyboard traversal, focus visibility, clipping and scroll reachability. For Windows native AI setup, test successful local response and failed/unavailable model; physical microphone dictation, stop/revoke and playback; explicit screen permission and contextual question, discard/revoke; meeting recording with consenting participants or synthetic content, transcription/manual notes separation and review before saving. Internal system audio remains optional source-mode only; verify the packaged candidate communicates unavailability. Measure startup, first token and full response with model/hardware noted, memory across repeated cycles and closure; never generalize synthetic results to native use. Verify installer candidate hashes, smoke tests and distribution policy before changing public release. No actual sensitive data in test fixtures or evidence.

## Proposed scoring rubric (not measured)
Each category is 0–10 using documented functional scenarios, visual inspection and measured benchmarks; weighted score is sum(score * weight)/100. Require overall >=9, no category below 8, and all critical gates (no unresolved critical/high severity issue, successful current regression/build, native core flows, explicit permissions and no silent data transfer). Unmeasured category means score withheld, not zero or ten.
- Visual identity and consistency 15%
- Usability of 50 tools 15%
- Accessibility and responsive layout 10%
- AI setup and conversation 15%
- Voice and screen 10%
- Meetings 10%
- Privacy and security 15%
- Performance and stability 10%

Next stage: final Windows homologation and current-commit CI evidence. Keep public installer unchanged until acceptance. Logo, dark default, existing 50 tools and free distribution policy remain unchanged by these commits.
