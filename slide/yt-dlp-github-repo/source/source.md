# Source Analysis

## Repo snapshot

- Source: https://github.com/yt-dlp/yt-dlp
- Snapshot date: 2026-06-01
- GitHub API snapshot: 167,014 stars.
- Latest stable release in the saved API response: `2026.03.17`.
- Official description: feature-rich command-line audio/video downloader.
- The README says yt-dlp supports thousands of sites and is a fork of youtube-dl based on the inactive youtube-dlc project.

## Facts useful for the deck

- Basic usage starts with `yt-dlp URL`.
- Audio extraction is available with `-x --audio-format mp3`.
- The README exposes playlist handling, format selection, subtitle, thumbnail, metadata, chapter splitting, SponsorBlock, browser cookie, JSON output, plugin, and Python embedding options.
- `ffmpeg` and `ffprobe` are highly recommended. They are required for merging separate video and audio files and for multiple post-processing tasks.
- The README documents `stable`, `nightly`, and `master` channels. It describes `nightly` as the recommended channel for regular users because website-side changes can break older releases.

## Caveat

- The deck should not imply that every media download is permitted. Users must confirm platform terms and content usage rights before downloading or reusing media.

## Local files

- `README.md`: saved raw README.
- `supportedsites.md`: saved supported sites list.
- `github-repo.json`: saved GitHub API repository snapshot.
- `latest-release.json`: saved latest stable release API response.
- `installation-wiki.html`: saved official installation wiki page.
- `banner.svg`: saved official yt-dlp banner asset.
- `github-mark.svg`: local GitHub mark reused for the open-source hero.
