# Aeris — Interaction design 001

Status: design accepted as a product direction; implementation and usability validation pending.

## Principle

The Hub is the administrative center, not a mandatory step for daily usage. Quick tools should be accessible with a single ordinary left click on a visible Aeris control, with minimal visual interruption. Do not open a window on every mouse click throughout the OS.

## Presentation modes

- Contextual icon: in supported browser fields, a small non-obstructive Aeris control appears on focus when the user has opted in for the site. Left click opens a local panel; explicit selection and preview precede authorized filling. No automatic form submission, password or banking data storage, hidden input capture, or bypass of site restrictions. Desktop contextual integration requires separate compatibility/security evaluation; no global mouse hook by default.
- Floating launcher: optional small button anchored to a chosen screen corner; left click opens a compact panel, second click or Escape closes it. Drag/reposition with an explicit gesture. Hidden by default until enabled; no always-on-top behavior over fullscreen by default.
- Quick panel (Spotlight): compact list of enabled/favorite tools only, opened from the launcher or a user-authorized shortcut. Open individual tools on demand; no background process per module.

## Configuration / proposed defaults

| Preference | Options | Proposed default |
| --- | --- | --- |
| Access mode | Contextual, floating icon, quick panel/shortcut, off; compatible modes can coexist | Quick panel on demand |
| Contextual icon | Enabled/disabled, per-site permission | Disabled |
| Floating icon | Enabled/disabled | Disabled |
| Screen corner | Bottom right, bottom left, top right, top left; custom position | Bottom right |
| Icon size | 24–64 logical px, with accessible hit target | 36 logical px |
| Panel size | Compact, normal, large, custom bounded width/height | Normal (320 x 420 logical px) |
| Panel appearance | Light/system/dark, opacity 80–100% if supported, readable contrast | System; opaque |
| Panel dismissal | Escape, close button, second launcher click, outside click if safely supported and no unsaved edits | Escape/close/second click |
| Fullscreen/gaming | Hide overlays; suspend optional services | Hide |
| Favorites | Explicitly chosen enabled modules | None until chosen |

Settings must include a live preview, save/reset controls, and non-sensitive local preferences. Never store a history of clicks or focused text. Panel placement must stay within the available work area, respect multiple monitors and DPI, avoid obscuring fields, and recover if the monitor configuration changes. Do not steal focus before explicit interaction. Keyboard access, contrast and readable sizing are required. Preserve drafts or request confirmation before dismissal if unsaved content exists.

## Implementation sequence

1. Foundation: generalize settings schema with backwards compatibility; build configurable quick panel/launcher inside Desktop, then implement the native optional floating entry point as part of Spotlight. Use event-driven UI; avoid global polling.
2. Snippets: reusable text with an explicit copy action; no automatic paste into third-party apps until a separately authorized integration is implemented.
3. Smart Automation: implement contextual Autofill in Chromium extension with minimal host permissions and explicit preview/confirmation. Evaluate native Windows field integration separately.
4. Validate mouse and keyboard use, resizing, bounds, multi-monitor/DPI, fullscreen behavior, idle resource usage and privacy. Test using fictitious profiles.

No performance, compatibility or feature-completion claim follows from this design document.

## Implementation status — a3

The Hub includes an appearance editor, a preview and an on-demand quick panel. The saved icon size affects the preview only. Position is relative to the Hub, clamped to primary-screen dimensions; opacity depends on window-manager support. The native floating icon, contextual autofill, custom sizes, themes, favorites, fullscreen detection and multi-monitor handling are not implemented yet. New tests are present but not executed.
