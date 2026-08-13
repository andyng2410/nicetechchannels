# Project Rules

These are the current project rules for agents working in this repo.

## Slide Workflow

- Read `WORKFLOW.md` before creating or substantially editing a slide project.
- Link Autopilot: when the user provides one or more links as slide source, or sends only a link without another stated intent, read the full `WORKFLOW.md` and required skills, then build the complete deck without stopping for script or visual-plan approval. Collect sources, choose the strongest narrative, write `script-90s.txt`, mark `visual-plan.md` as `AUTO-APPROVED`, implement, validate, capture, inspect, and fix through handoff. Ask only for inaccessible/insufficient source or high-risk claim, asset-rights, cost, or irreversible decisions. If the user explicitly asks only to summarize, analyze, or save the link, follow that intent instead.
- For external sources, use `skills/source-assets/SKILL.md` before writing script or DOM; source collection must include text/facts, local visual assets, and `source/source.md` inventory.
- For X/Twitter, use `skills/x-sources/SKILL.md` first for `bird`/X media extraction — always include `bird read --json-full` for post/article images, then finish with `source-assets`.
- For X/Twitter media, use only author-posted media or media from links shared by that author; avoid media from comments/replies unless explicitly requested.
- Verify logo/media file types render correctly (`file <path>`) before use; check pricing/quota/promo claims against the original help/blog page and state the mechanism plainly in the script (what still burns quota, what costs extra, what happens after the deadline).
- Before writing/revising `script-90s.txt`, read `script-writing/START_HERE.md`, `SCRIPT_RULES.md`, `STYLE_INDEX.md`, plus relevant `style*.md` files.
- If the user has not fixed tone/script, propose usually 5 complete `script-90s` drafts in a compact table (`Bản | Style | Hook`). After selection, present the final script as `Slide | Voiceover | Reveals` before writing `script-90s.txt`.
- Vietnamese is default for script and slide text. Keep English for names and technical terms when clearer.
- Script pacing: slide 1 is one punchy hook; later explanatory slides usually have 3-4 short/medium sentences, with the first sentence as a short visual beat.
- Do not use the em dash `—` in `script-90s.txt` or `slideScripts`; use commas, colons, or shorter sentences for cleaner TTS.
- Do not create or hand-edit `upload-metadata.json` while building a deck; Upload Center/server generates metadata when needed.
- After final script, create/update `visual-plan.md`; present compact table `Slide | Nội dung voice | Reveals | Visual`. Do not put phone-unreadable source images in the Visual column — use custom scenes instead. See `WORKFLOW.md` §3.
- If the user asks to chốt script and visual plan together, the first response must paste both approval tables in chat: `Slide | Voiceover | Reveals` and `Slide | Nội dung voice | Reveals | Visual`; do not only write files or start DOM/CSS before approval unless explicitly told to skip review.
- In `visual-plan.md`, slide 2 onward must pass the visual-first gate: scene primitive, creative angle, motion/animation illustration, color roles/adjacent variation, and anti text-box/card check.
- Before DOM/CSS visual work, use `skills/slide-visuals/SKILL.md`; slide 1 hero templates are fixed-copy, while later visual/animation patterns are references that can be copied, remixed, or replaced with a stronger content-specific scene.

## Visual Defaults

- Copy from `template/escbase-slide-starter`.
- Keep grid off, `backgroundFx: "particles"`, subtitle `fontSize: 18`, `bottom: 172`, `maxLines: 1`, custom BGM `meta.mp3`, and safezone `100px 28px 200px` unless user asks otherwise.
- New decks must include the actual `preview-assets/bgm/meta.mp3` file from starter, not only JSON/app references to it. Missing custom BGM is a handoff defect.
- Demo/source videos embedded in slides are muted by default so they do not fight the voiceover or BGM. Only enable original video audio when that audio is the main content and the user explicitly approves it; if enabled, keep BGM from overlapping it.
- Do not start `web_server.py` unless user asks.
- Source media must be local, full-frame, uncropped, and undistorted by default. Use `object-fit: contain`, but match the media container/frame to the asset aspect ratio or scale the media to the correct full safezone width. Do not leave black pillarbox/letterbox bands from the slide background unless those bars are already in the source file or explicitly approved by the user; crop only when explicitly requested.
- Media-first tie-breaker: when source media is the proof, readability on `390×693` wins over filling every gap. Let media take the full safezone width when possible; do not shrink it just to fit extra labels or side visuals.
- Do not place overlays on source images or videos — no scan lines, badges, captions, chips, gradients, or pseudo-elements on top of the media frame. Source attribution goes **below** the image/video, not stacked on it. Semantic animation on media-first slides uses elements **outside** the media frame (chip rails, metrics, pipelines), not scrims or motion drawn over the media.
- If media already uses most of the safezone and would make other reveal visuals small or unclear, split the beat: keep the media reveal clean, then hide it on later reveals and use the full safezone for a custom scene or semantic animation.
- Use the remaining safezone as the real canvas. Undersized visuals, broad dead space, unreadable phone labels, and disconnected top/bottom clusters are defects.
- Default typography/color/density follows `template/visual-pattern-gallery/` and the Alex-style reference: large readable text, color with clear semantic roles, and a main visual that fills the safezone. Tiny text, one-note color, or empty safezone space are defects.
- Deck visuals should use varied, intentional role colors across slides; a one-tone palette across the contact sheet is a defect.
- Adjacent explanatory slides should vary shape, motion, or role color; repeated box/card layouts are a defect even when text is short.
- Brand/product slides should include a logo/mark when possible; save assets locally.

## Visual-First Rule

- `skills/slide-visuals/SKILL.md` is the source of truth for visual planning, slide 1 templates, semantic animation, typography/color, and phone-density QA.
- `template/visual-pattern-gallery/` is the index for slide 1 hero templates plus later-slide typography, density, color-role, and animation references.
- Slide 1 must copy the full slide 1 from the canonical matching template, then replace only text/logo/media/source. Do not rebuild it, redesign the hero, or change its layout/background/style.
- Slide 1 must include copy proof in `visual-plan.md`: `Copied from`, `Allowed replacements`, and `Intentional deviations`. Default deviations are `none`; unapproved layout/background/style/effect changes fail QA.
- Canonical slide 1: GitHub repo from `template/openmontage-github-trending/`, source-image from `template/googleaistudio-post-2069450021955592406/`, logo/avatar from `template/kimi-moonshot-post-2066467110960959833/` or `template/addyosmani-loop-engineering/`.
- Slide 2 onward may copy/remix gallery patterns or use a custom scene, but must pass the `WORKFLOW.md`/`slide-visuals` visual-first gate.
- Copying gallery visual patterns must not remove or replace the starter `preview-assets/bgm/meta.mp3`.
- Do not restate narration with stacks of text cards; use visuals, source artifacts, metrics, icons, and short labels.
- Since subtitles already carry the narration, keep canvas text minimal and prioritize visual animation. It is fine to combine multiple visual parts inside one reveal and sequence their motion within the safezone instead of spreading them into small disconnected clusters.
- Slide 1 headline defaults to the OpenMontage/GitHub repo hero size, about `42px` at `390x693`; only shrink it when the title truly overflows or overlaps after checking.
- Later slides must still obey hard visual standards: large readable phone-scale text, color with clear semantic roles, main visual filling the safezone, and content-specific semantic animation. For media-first slides, use the media-first tie-breaker above.
- Cards are allowed only when they are meaningful artifacts such as terminal output, source proof, metric, warning, or pipeline node.

## Verification

- Before handoff, run `.venv/bin/python validate_slide.py slide/<project> --semantic-report`.
- After PASS, capture every slide with `.venv/bin/python capture_slides.py slide/<project>` (390x693, all reveals, panels hidden) and inspect each image manually.
- Compare slide 1 screenshot against the canonical template; unapproved deviations fail.
- Also watch the animated preview for explanatory slides for a few seconds.
- Fix overlap, tiny labels, dead safezone space, black pillarbox/letterbox bands from wrong media frame ratios, repeated card stacks, text-box layouts, one-tone color palettes, missing semantic animation, and unclear final states before handoff.
- Do contact-sheet squint/color and motion/animation passes: each explanatory slide should read as a distinct moving scene, not the same box layout with different words.
- Report clearly: validate PASS, mapping PASS, safezone PASS, and semantic 1:1 reviewed. If anything was skipped, say so.

## General Agent Rules

- Read before writing. Inspect local files, source material, immediate callers, and shared utilities before changing anything substantial.
- Keep changes surgical and simple. Do not refactor, reformat, or clean unrelated files.
- Prefer the repo's existing patterns and tools.
- Define success criteria, execute, verify, and fail loud when blocked.
- Use deterministic tools for deterministic work; use the model for judgment, drafting, classification, and summarization.
- Surface conflicts instead of blending them. Prefer newer, more explicit, more tested rules.
- Keep token/time budget visible on large tasks; summarize and ask for a fresh session if context gets risky.
- Do not regenerate paid ElevenLabs audio or use `--force` unless user explicitly asks.

## Persistent Learning

- When the user corrects a repeated workflow preference, update `WORKFLOW.md` and, if it should affect future agents immediately, update `AGENTS.md`.
- Keep project rules concise and practical; do not add a large harness unless explicitly asked.
