# Source Notes: bird.fast CLI

## Sources

- Landing page: https://bird.fast/
- npm package: https://www.npmjs.com/package/@steipete/bird
- Author profile: https://github.com/steipete
- Former repository URL: https://github.com/steipete/bird

## Verified Facts

- `bird` is a CLI for X/Twitter using cookie authentication and X web GraphQL endpoints.
- Landing page commands include tweet, reply, read, thread, search, mentions, and DMs.
- Packaged npm README also documents replies, bookmarks, likes, home timeline, news, lists, followers, following, follow/unfollow, engagement actions, and media uploads.
- Cookie authentication can use an existing Safari, Chrome, or Firefox session. `bird whoami` prints the authenticated account and `bird check` shows credential availability.
- The packaged client requires both `auth_token` and `ct0`. They can be passed as CLI flags or environment variables. The recommended script angle uses masked placeholders only and explicitly warns users that these cookies are sensitive.
- Human-readable output is the default. `--json` and `--plain` are available for scripts and agents.
- Installation commands include `npm install -g @steipete/bird` and `brew install steipete/tap/bird`.
- npm package snapshot checked on 2026-06-02: latest version `0.8.0`, published 2026-01-19.
- The former GitHub repository URL currently returns `404`. The author's GitHub profile describes `bird` as private: "had to make it private."
- The packaged README warns that X can change undocumented endpoints and query IDs without notice and that internal endpoints can be rate limited.

## Script Angle

Present `bird` as a practical CLI to give an agent controlled access to X workflows. Keep the warnings explicit: use a secondary account, confirm before write actions, protect `auth_token` and `ct0`, and do not treat an undocumented API as stable infrastructure.
