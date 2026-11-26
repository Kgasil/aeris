# ClamAV definition recovery — isolated validation

Previous run [45892124629](https://github.com/Kgasil/aeris/actions/runs/45892124629), candidate 985c50e9865ddc1f241fee131db505e2994455a5, evidence artifact 15152551149, ZIP SHA-256 6207d72e6f025900ed0749b46280894b9638eaabadd2eebc800bcd3f1e2ebd4b independently verified, CRC clean. FreshClam downloaded remote version 28194. sigtool verified its signature; build timestamp 2026-11-25T06:26Z, age 137544 seconds, exceeds 86400. No candidate scan executed. Post-attempt hashes unchanged. This is not evidence of infection or clearance.

The isolated branch avoids triggering the existing regression and interface workflows. First verify official DNS TXT (diagnostic), download the pinned official scanner and use FreshClam with official CDN and DNS. No unofficial mirrors, no forced downloads, no rate-limit bypass, no loosening of the 24h requirement. If preflight is inconclusive, skip all build/assurance/homologation/scan steps. If verified fresh, build once from the unchanged app source (prior binaries were not retained), preserving mandatory build tests, verify packages and run the scan using the already prepared database on the same runner. Recheck signature and freshness before and throughout scanning. Collect only evidence, not public binaries. No release, signature certification, or gate approval. This new procedure has not yet run on Windows.

Official guidance: https://docs.clamav.net/faq/faq-troubleshoot.html and https://docs.clamav.net/faq/faq-freshclam.html . Repeated downloads cannot generate newer upstream signatures. If the official base remains stale, stop and defer until a new official version exists. No automated recurring download configured.

All app code and the public branch remain unchanged. Existing formal gate is unchanged; preparation does not authorize public distribution.

## Recovery execution 45892912161

- Workflow succeeded in enforcing the preflight, not in scanning binaries: https://github.com/Kgasil/aeris/actions/runs/45892912161 . Evidence artifact 15151928105: SHA-256 `93c474411a9a2db40252570e550804a3468c0961b882c9808c68b978ebdf6c34` verified independently, ZIP CRC clean.
- Official DNS TXT for current.cvd.clamav.net advertised daily version 28194; FreshClam downloaded that version and sigtool reported Verification OK. Daily database build 2026-11-25T06:26:00Z, age 137781 seconds (38h16m21s) at preflight. Pinned scanner archive hash verified. Freshness limit remains 86400 seconds.
- Result INCONCLUSIVE: no candidate compiled, no installer homologated in this run, no package scanned, no binary retained. The previous candidate's homologation remains historical evidence only. This is an upstream freshness blocker, not an application defect or a malware detection. No repeated download or rebuild was initiated. Recheck after the official publisher supplies a fresh database; the same preflight will enforce freshness again. All existing release gates and restrictions remain unchanged.

## Lightweight update probe
The last observed official TXT record advertised 28194. Added a DNS-only probe before downloading ClamAV. An unchanged, older, malformed or unavailable record skips the scanner download and all builds. A newer advertised version only enables the existing FreshClam preflight; signed database freshness must still be verified, and all scan and integrity requirements remain in force. The probe-request text file permits an isolated on-demand check without touching app files or main. No automatic release; outstanding formal gates remain.
