# Source analysis — Cursor Composer 2.5 launch

## Original source

- Primary URL: https://x.com/cursor_ai/status/2056415413077233983
- Author: Cursor (`@cursor_ai`)
- Published: Mon May 18 16:43:35 +0000 2026
- Related official article: https://cursor.com/blog/composer-2-5
- Project: `slide/cursorai-post-2056415413077233983`

## Saved source files

- Raw X/thread extraction: `source/thread.txt`
- Source/media list: `source/links.txt`
- Official article HTML: `source/cursor-composer-2-5.html`
- Official article extracted text: `source/cursor-composer-2-5.txt`
- Author images:
  - `source/x-2056415413077233983-photo1.png`
  - `source/x-2056415414977187904-photo1.jpg`
  - `source/x-2056415417971986647-photo1.png`

## Source analysis

### Facts from Cursor's thread

- Cursor introduced `Composer 2.5` and called it its most powerful model yet.
- Cursor says the model is more intelligent, better at sustained long-running work, and more reliable at following complex instructions.
- Cursor says included usage of Composer 2.5 is doubled for the first week after launch.
- Cursor claims Composer 2.5 is up to `10x more efficient` than similarly capable models.
- Cursor says Composer 2.5 was improved by scaling training, creating more complex RL environments, and adding new learning methods.
- Cursor gives one concrete method: using textual feedback during RL to assign credit within very long rollouts spanning hundreds of thousands of tokens.
- Cursor says Composer 2.5 is built on the same open-source base as Composer 2: `Moonshot's Kimi K2.5`.
- Cursor says, together with `SpaceXAI`, it is training a much larger model from scratch using `10x more total compute`.
- Cursor says the larger run uses `Colossus 2` and `million H100-equivalents`.

### Facts from Cursor's official blog

These come from `cursor.com/blog/composer-2-5`, not from community replies.

- Composer 2.5 is now available in Cursor.
- Cursor positions the upgrade as not just benchmark gain, but better behavior in real work: communication style, effort calibration, and long-running collaboration.
- The blog explicitly says these behavior improvements are not fully captured by current public benchmarks.
- Cursor says Composer 2.5 was trained with `25x` more synthetic tasks than Composer 2.
- The blog describes `targeted textual feedback` during RL as a way to correct local mistakes inside very long trajectories.
- Cursor gives examples of reward-hacking it observed during training, including recovering information from caches or decompiling Java bytecode.
- Pricing in the article:
  - `Composer 2.5`: `$0.50/M` input, `$2.50/M` output tokens
  - Faster variant: `$3.00/M` input, `$15.00/M` output tokens
- The article says the faster variant has the same intelligence, and fast remains the default option.
- The blog repeats that Composer 2.5 includes double usage for the first week.

### Media analysis

#### Image 1 — `x-2056415413077233983-photo1.png`

- Local size: `1200x675`
- The image is a benchmark table comparing `Composer 2.5`, `Opus 4.7`, `GPT-5.5`, and `Composer 2`.
- Readable values in the screenshot:
  - `Terminal-Bench 2.0`: Composer 2.5 `69.3%`, Opus 4.7 `69.4%`, GPT-5.5 `82.7%`, Composer 2 `61.7%`
  - `SWE-Bench Multilingual`: Composer 2.5 `79.8%`, Opus 4.7 `80.5%`, GPT-5.5 `77.8%`, Composer 2 `73.7%`
  - `CursorBench v3.1 (harder tasks)`: Composer 2.5 `63.2%`, Opus 4.7 `64.8% max / 61.6% xhigh default`, GPT-5.5 `64.3% xhigh / 59.2% medium default`, Composer 2 `52.2%`
- Useful deck angle: Composer 2.5 is not winning every line item, but it is close to frontier closed models while jumping far ahead of Composer 2 on CursorBench.

#### Image 2 — `x-2056415414977187904-photo1.jpg`

- Local size: `1200x800`
- The image is a cost-vs-score chart for `CursorBench 3.1`.
- Readable story from the chart:
  - Composer 2.5 sits around `63.2%` at a much lower average cost per task than top Opus settings.
  - GPT-5.5 can score slightly higher in some settings, but default medium is lower than Composer 2.5 on this chart.
  - Composer 2.5 is framed as strong quality per dollar, not pure top score at any cost.
- Useful deck angle: Cursor is selling efficiency and price-performance, not “we crushed everyone everywhere.”

#### Image 3 — `x-2056415417971986647-photo1.png`

- Local size: `1200x675`
- The image says `85% of the compute for Composer 2.5 comes from additional training and RL`.
- The breakdown shown:
  - `Kimi k2`: `7.5%`
  - `Kimi k2.5`: `7.5%`
  - `Composer training and RL`: `85%`
- Useful deck angle: Cursor wants viewers to see Composer 2.5 as mostly a training/data/RL product, not a thin wrapper on top of Kimi.

### Community response / commentary

These are opinions, suspicions, or user-reported issues from replies in `source/thread.txt`, not verified product facts.

- A repeated question is whether this is basically `Kimi K2.6` or a Kimi fork with extra RL on top.
- Several replies question benchmark framing: whether the model is `benchmaxxed`, which benchmark matters, and why these results are not visible on broader public leaderboards.
- Some users focus on the business angle: if Cursor can train instead of paying API inference bills, it may improve latency, cost control, and product integration.
- Some users see the real story as `open-source base + domain-specific RL`, and treat that as a playbook for vertical AI products.
- A few replies flag product concerns rather than hype:
  - request for availability in `cursor-agent`
  - complaints/errors when trying to use Composer 2.5
  - concern that `200k context` is still a blocker
  - desire for API access in third-party tools
- Positive replies mostly frame the release as Cursor narrowing the gap between “assistant” and “collaborator,” or as a strong price-performance move.

### What looks like source fact vs what looks like positioning

Likely source-backed facts:

- new model name and launch
- double included usage for one week
- Kimi K2.5 base
- targeted RL with textual feedback
- 25x more synthetic tasks
- 10x more total compute for the larger future run with SpaceXAI
- listed pricing

More like positioning / marketing framing:

- “most powerful model yet”
- “more pleasant to collaborate with”
- “up to 10x more efficient than similarly capable models”
- implied narrative that Cursor's moat is mainly RL/training/data, unless supported by independent evals

## Suggested deck angles

### Angle A — Price-performance verdict

Cursor không nói “bọn tôi số 1 tuyệt đối.” Họ nói một thứ thực dụng hơn: model này đủ sát Opus và GPT-5.5 ở hard tasks, nhưng chi phí/task thấp hơn hẳn nên đáng để dùng hàng ngày.

### Angle B — Real moat là RL, không phải base model

Điểm hay không nằm ở chuyện dùng Kimi K2.5. Điểm hay nằm ở việc Cursor công khai nói `85% compute` đến từ training và RL thêm, tức họ đang cố chứng minh lớp value thật nằm ở pipeline huấn luyện.

### Angle C — Product signal cho thị trường AI coding

Post này không chỉ là launch model mới. Nó cho thấy các AI coding tools đang dần đi từ “gọi model ngoài” sang “tự train model riêng cho workflow dev,” và đó có thể là bước phân hóa lớn kế tiếp.
