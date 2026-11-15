# Current operating policy

The repository now defaults to approved automated runs with evidence-based recordkeeping in AGENTS.md and SOP.md. The historical automated tests below describe earlier technical evidence, not manual completion records or authorization to select active mode. CI continues to check infrastructure without Instagram login or engagement.

# Validation status

## Known live evidence

On 2026-11-14, AliasMode 0.1.0-beta.74 on macOS Firefox, the fixed soft engine completed a short test through Home, notifications, inbox, feed, search, profile visits, topic items, normal Reels feed and return Home. Actual summary: 2 counted topic items, 3 profile visits, zero likes/follows/saves/stories. It skipped 16 nonmatching feed items. This was a short test, not a completed full-length production routine.

The active plan is supplied and preloaded but has not been validated live. Do not infer that browser UI actions in active mode work merely because passive browsing passed. Linux/container verification is recorded separately below.

## Automated checks

Five Node regression cases cover direct section navigation and hidden-author handling. Seven Python cases cover script seeding without overwriting edits/corrupt stores, profile reuse, explicit Firefox creation without credentials, paginated profile discovery, and Local-mode initialization that preserves existing configuration. These use narrow test doubles and do not simulate Instagram end to end.

The container must be built and its desktop/app startup checked independently. A graphical startup test does not establish that login, every Instagram DOM selector, or active actions work on every machine.

## Container acceptance, 2026-11-14

[GitHub Actions run 43549151508](https://github.com/kofiowusuai-lab/instagram-aliasmode-kit/actions/runs/43549151508) passed on x64 Ubuntu at commit `5a2631b`:

- Seven Python tests, five Node regression tests, script syntax checks and Compose validation passed.
- Docker image built successfully and verified the pinned official AliasMode archive checksum.
- Fresh container startup served noVNC, returned a successful AliasMode API response, created the initial profile and reported its browser as Active.
- All three private scripts were present in the script store. No Instagram credentials were entered and no engagement was performed by this CI check.

The same image also built locally on Apple Silicon, but the AliasMode Linux sidecar failed during startup under ARM emulation. Container support is therefore x64; native AliasMode is the Mac/ARM fallback. No claim of a live Linux Instagram warm-up or active engagement test is made.

## Scheduler validation, 2026-11-14

The fixed-GMT scheduling implementation passes 15 Python and 9 Node checks, including persisted skip dates, no duplicate claims, missed slots, pause behavior, immediate warning persistence despite a later API error, budget clipping, and dedicated-tab isolation. A live no-engagement AliasMode runtime probe confirmed node:fs imports and creation/closure of an about:blank tab. The timed source was provisioned and its exact saved source verified.

The owner account's native macOS minute-tick LaunchAgent was installed and its initial no-due-session tick exited 0. Private settings/state are not committed. No full 20-minute scheduled Instagram session has yet completed in this evidence. This scheduler uses the native background browser, not a verified headless mode. Container startup acceptance above predates the scheduler addition; it does not establish unattended engagement correctness.
# Phone backend validation — 2026-11-15

Phone Harness 0.3.3 was installed on macOS 26.5. Its doctor reported the Python frameworks, Accessibility and Screen Recording available; iPhone Mirroring was not yet running/paired. No live Instagram phone activity or account switch was performed. Backend tests simulate UI observations and time. Pairing, screenshot-based navigation calibration, an attended passive session and LaunchAgent phone execution remain unverified until actual evidence is recorded. Existing Instagram warnings must remain paused.
