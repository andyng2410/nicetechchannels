# NiceTechChannels Slide Starter

Copy this folder for new decks unless the user explicitly requests a different template.

Keep these defaults unless asked otherwise:

- `preview-settings.json` subtitles: `enabled: true`, `fontSize: 18`, `bottom: 172`, `maxLines: 1`.
- BGM: custom `preview-assets/bgm/meta.mp3`, volume `0.3`.
- New decks must contain the real `preview-assets/bgm/meta.mp3` file, not just JSON/app references to that path.
- Grid overlay disabled.
- Preview background effect: `backgroundFx: "scan"`; keep the starter mixed per-slide canvas FX unless content requires a change.
- TikTok safezone for normal slide content: `100px 28px 200px` via `pixelle-slide-content`.
- Keep script sentence counts matched to reveal units.
- Replace placeholder source notes in `source/source.md` before writing final deck content.

When copied to `slide/<project>/`, update:

- `index.html` title/meta and slide DOM text/media.
- `script-90s.txt` and `slideScripts` in `app.js` with identical text.
- `preview-settings.json` BGM URL/path only if the copied asset path changes.
- If using the default custom BGM, verify `preview-assets/bgm/meta.mp3` exists before handoff.

## Outro slide (`data-outro`)

The last slide (`data-slide="6"`, marker `data-outro="1"`) is the fixed branded outro:

- Keep its DOM, CSS (`.outro-*` block at the end of `style.css`), copy, and animations EXACTLY as in the starter. Do not redesign, retheme, or "improve" it per deck.
- Brand exception: when `config/branding.json` overrides the defaults, replace ONLY the channel name, tagline, and the `.brand-top-left`/`.brand-bottom-right` handle text with the configured values (the outro voiceover line follows the configured brand automatically). When the config sets a `logo`, copy that file into the deck OVERWRITING `logo-nicetechchannels.ico` — keep the file name, do not touch DOM `src` attributes. Everything else stays fixed.
- Keep the outro script line (last line of `script-90s.txt` / `slideScripts`) verbatim: `Hãy theo dõi ngay NiceTechChannels. Đăng ký kênh để không bỏ lỡ những tin tức mới nhất về công nghệ và AI.`
- The outro is exempt from the visual-first gate, adjacent-slide variation, and color-diversity checks: it is intentionally identical across every deck (neutral dark background, YouTube-red subscribe button, TikTok-style follow badge).
- Its colors are hardcoded on purpose (no theme vars) so deck palette changes never leak into the outro.
- When adding content slides, insert them BEFORE the outro slide and renumber `data-slide` so the outro stays last; the outro script line stays the last line.
