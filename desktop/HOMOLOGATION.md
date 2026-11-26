# Aeris Homologation — 1.1.0rc1

## Verified historical build

Commit 2ce13cd517bc923657880f33be4a81523af699c0.
Run https://github.com/Kgasil/aeris/actions/runs/45881755549: all 3 jobs succeeded.
537 tests per suite: Linux Python 3.12 525 passed/12 skipped; Windows Python 3.12 and 3.14 each 533 passed/4 skipped. No failures. Integrated and packaged smoke checks passed. Inno Setup produced an unsigned installer; portable bundle verification counted 47 members.

Downloaded evidence artifact 15147504524 (15,898 bytes), ZIP CRC test passed and locally calculated SHA-256 exactly matched the GitHub metadata: 3855ae544700e7d91a9d88bc6a856e177f507dd1c8fc311e51b74e559f4752c7. Inventory and SHA256SUMS.txt agree:
- Setup.exe: 12,892,224 bytes; b904450ed73ee485f233e152f59233acbae00ebb920c68e0a14ca6ab715fb6e9.
- portable.zip: 13,865,732 bytes; 4b64070f571fc923c02abc901665646b39d1d843783f936120807560e7cd215f.
- Aeris.exe: ea555fa11d29c4eec9b3d0af55b0e4425cd192cd487b6ac4dc0ff308bddc39f2.

These are recorded hashes of the historical build, NOT recalculated from its binary files: only evidence was retained. The repository is public, so do not upload unsigned candidate binaries as downloadable CI artifacts or publish a release without approval.

## Visual evidence and confirmed correction

Downloaded and inspected home, catalog and screen images from https://github.com/Kgasil/aeris/actions/runs/45881755670/artifacts/15148545531. In the 1024x768 screenshot, context view clipped voice and advanced buttons and bottom discard control. Raised the compact breakpoint from 930 to 1100 px, widened context text wrapping, reserved status space, and added visibility/height assertions at 980x660. New regression and actual screenshot verification still required. Historical successful build does not validate these new changes.

## Controlled test

distribution/homologate-candidate.ps1 runs only on a GitHub-hosted Windows x64 runner, refusing existing installation or data. The candidate-build job first rebuilds after successful Windows/Linux regressions, then checks both package hashes/size against inventory and checksums, installs the freshly built unsigned installer, compares installed executable and portable manifest files, runs installed UI self-test, reinstalls the same version and uninstalls, verifying preservation of a synthetic data marker. This is not a cross-version upgrade test, non-admin Windows client clean VM, actual microphone/AI test, independent license audit or malware certification. Only reports/logs retained. No executable distributed. The script and job have not yet completed; do not claim pass.

## Release decision

Keep all formal release criteria pending until evidence for the final candidate is reviewed. Still need actual Windows 10/11 clean VM tests including upgrade from public version and non-admin behavior, real devices and models, performance/accessibility, license and trust review, antimalware and signing strategy, final binary hash and approval. Preserve main and existing public release. No publication. No new functionality added.
