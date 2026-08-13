# Source notes - calesthio/OpenMontage

Snapshot date: 2026-06-24, Asia/Ho_Chi_Minh.

## Primary sources saved

- `README.md`: raw README from `calesthio/OpenMontage`.
- `AGENT_GUIDE.md`: raw agent operating guide from the repo.
- `repo.json`: GitHub API snapshot for repo metadata and metrics.
- `languages.json`: GitHub languages API snapshot.
- `topics.json`: GitHub topics API snapshot.
- `tree.json`: GitHub repository root contents API snapshot.
- `tree-recursive.json`: GitHub recursive tree snapshot used to sanity-check pipeline and skill counts.
- `github-trending-daily.html`: saved GitHub Trending daily page.
- `logo.png`: repo logo asset, saved from `assets/logo.png` but file content is JPEG.
- `showcase.jpg`: repo showcase image from `assets/showcase.jpg`.
- `signal-from-tomorrow-demo.mp4`: 30s demo video from `assets/signal-from-tomorrow-demo.mp4`.
- `demo-videos/`: six GitHub README embedded demo videos downloaded from GitHub user-attachments.
- `demo-videos/posters/`: poster frames extracted from the downloaded demo videos for stable preview frames.
- `links.txt`: source URLs.

## Numeric facts

- GitHub API snapshot: 15,954 stars, 1,890 forks, 98 open issues, main language Python, AGPL-3.0 license.
- Saved GitHub Trending daily HTML: `calesthio/OpenMontage` appears on daily trending with 15,955 stars, 1,890 forks, and 3,592 stars today.
- Repo description on GitHub says: 12 pipelines, 52 tools, and 500+ agent skills.
- README feature list says 12 production pipelines, 52 production tools, and 400+ agent skills.
- Recursive tree snapshot has 13 YAML files under `pipeline_defs/`; one appears to be `framework-smoke.yaml`, so the public "12 production pipelines" claim is likely excluding a smoke/test pipeline.
- Recursive tree snapshot has 546 markdown skill files under `skills/` and `.agents/skills/`, which supports the current 500+ skill claim.
- Languages API: Python dominates, with TypeScript, JavaScript, Shell, and Makefile also present.
- `signal-from-tomorrow-demo.mp4`: 1920x1080, 30.06s, video plus AAC stereo audio.

Numbers are a time-specific snapshot and may continue changing after capture.

## Facts from README

- OpenMontage describes itself as the first open-source, agentic video production system.
- The repo frames the product as turning an AI coding assistant into a full video production studio.
- The core workflow can handle research, scripting, asset generation, editing, and final composition.
- The README stresses a distinction between image-based video and "real video video": documentary montage can build a corpus from free stock footage and open archives, retrieve motion clips, edit them into a timeline, and render a finished piece.
- It supports starting from a YouTube video, Short, Reel, TikTok, or local clip, then analyzing transcript, pacing, scenes, keyframes, and style before producing concepts, tool path, cost estimates, and a sample.
- Quick start prerequisites: Python 3.10+, FFmpeg, Node.js 18+, and an AI coding assistant such as Claude Code, Cursor, Copilot, Windsurf, or Codex.
- Zero-key path includes Piper TTS, open footage from Archive.org/NASA/Wikimedia Commons, optional free-key stock sources, Remotion, HyperFrames, FFmpeg, and built-in subtitles.
- README examples include low-cost productions such as $0.15 image-based animations, $0.69 OpenAI-only product ad, and $1.33 Kling/fal.ai animation; these are examples, not guaranteed costs.
- Pipeline stage flow is `research -> proposal -> script -> scene_plan -> assets -> edit -> compose`.
- Each stage has a director skill; the agent reads the skill, uses tools, self-reviews, checkpoints state, and asks for approval at creative decision points.
- Quality gates include pre-compose validation, post-render self-review, slideshow risk scoring, source media inspection, provider selection scoring, decision logs, and budget controls.
- Agent compatibility files exist for Claude Code, Cursor, GitHub Copilot, Codex, and Windsurf.
- Local LLM support via Ollama and LM Studio is marked "coming soon" in the README.

## Facts from AGENT_GUIDE

- OpenMontage is instruction-driven: the AI agent is the orchestrator, while Python provides tools and persistence.
- Agents should not improvise the production workflow; real work goes through `pipeline_defs/`, `skills/pipelines/`, and the tool registry.
- The guide says not to write ad-hoc Python scripts to call tools directly, not to bypass preflight/checkpoints/review, and not to generate assets without reading the relevant director skill.
- It emphasizes human approval for creative stages and material provider/runtime changes.

## Media saved

- `logo.png`: useful for a first-slide logo/mark, but it is JPEG data with a `.png` extension.
- `showcase.jpg`: 1920x720 overview image, useful as a source artifact or wide visual strip.
- `signal-from-tomorrow-demo.mp4`: 30s demo with audio, useful as an immediate post-hook demo slide if the deck later uses media.
- `demo-videos/01-signal-from-tomorrow-user-attachment.mp4`: 1920x1080, 30.06s, GitHub README demo for "SIGNAL FROM TOMORROW".
- `demo-videos/02-last-banana.mp4`: 540x960, 60.05s, GitHub README demo for "THE LAST BANANA".
- `demo-videos/03-void-neural-interface.mp4`: 1920x1080, 48.57s, GitHub README demo for "VOID - Neural Interface".
- `demo-videos/04-afternoon-in-candyland.mp4`: 1280x720, 30.06s, GitHub README demo for "Afternoon in Candyland".
- `demo-videos/05-mori-no-seishin.mp4`: 1280x720, 30.06s, GitHub README demo for "Mori no Seishin".
- `demo-videos/06-into-the-abyss.mp4`: 1280x720, 30.06s, GitHub README demo for "Into the Abyss".

## Caveats for script

- Do not present OpenMontage as a one-click consumer app; setup needs Python, FFmpeg, Node.js, and an AI coding assistant that can run the repo.
- Do not imply all premium generation is free; many providers require API keys and can spend money.
- Do not overclaim "first" as an independently verified fact; it is the repo's self-description.
- Do not treat example video costs as guaranteed costs.
- Do not call it a CapCut/Premiere replacement; better framing is an agentic production framework/pipeline.
- Mention AGPL-3.0 carefully if talking to builders who might embed it in closed products.
- Avoid exact "400+" vs "500+" conflict in spoken copy unless attributing to a specific source. "Hơn 500 skill file trong snapshot tree" is safe from the saved tree.

## Slide angle

- Strong hook: this is not another prompt-to-clip generator; it tries to make the whole video production workflow executable by an agent.
- Strong proof: the repo is hot on GitHub Trending, with nearly 16k stars and 3.5k+ stars today in the saved snapshot.
- Strong value: pipeline-first production, reference video analysis, real-footage documentary path, quality gates, decision logs, and budget controls.
- Balanced caveat: powerful for agent-literate users, but still a repo-driven workflow with setup and provider/API choices, not a consumer one-click app.
