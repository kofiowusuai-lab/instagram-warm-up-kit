# Operating workflow

## Native phone workflow

For Instagram in the real iPhone app, use [PHONE.md](PHONE.md) instead of the browser installation below. Phone Harness runs on the host Mac, not inside the x64 AliasMode container. Keep existing per-account records authoritative. Setup does not authorize engagement, clear warnings, migrate sessions or install a new schedule. The account's explicit `execution_backend` selects the runner; missing means AliasMode for compatibility.

## First installation

Use the README quick start. The container stores AliasMode at `/opt/aliasmode`, the kit at `/opt/kit`, and account state under `/data`. Scripts are seeded before AliasMode starts into `/data/com.aliasmode.desktop/custom-scripts/local.json`. Existing copies are never overwritten. Fresh installations also receive a Local-mode config before app startup; existing configs are preserved. Bootstrap uses only the documented loopback status/profile/browser routes; it explicitly creates Firefox rather than the API's Chromium default. It reuses a matching profile name and handles list pagination.

If AliasMode displays welcome/local-mode onboarding, complete it in the desktop. If the initial-profile task timed out, rerun `docker compose exec desktop python3 tools/bootstrap_profile.py`. It never handles Instagram credentials. Check the actual browser window and navigate to Instagram manually if browser launch arguments are ignored by a future platform release.

## Account management

The current default is automated activity with evidence-based records, defined in AGENTS.md and SOP.md. Create a separate named AliasMode profile and a private record directory for each account. Let the user sign in and complete verification. Copy the five root starter files into the account directory only if absent. Use ignored `accounts/<label>/` on the host or persistent `/data/manager/accounts/<label>/` in the container; choose one authority per account.

Confirm timezone, start date and intended schedule. Read all five files before each plan. Execute within the approved script mode and schedule, then update logs, progress and warnings from observed run results. Obtain user reports only for activity outside the observed run. Review each seven-day period and save a weekly report. Missing reports are unreported, never assumed zero or skipped. Follow the supplied report formats.

Run only the authorized script mode on the intended account. Default to tested soft mode; do not silently advance to active. Code tests and container readiness checks can run; they are infrastructure verification and do not establish manual activity or account readiness. Do not infer that older automated test history authorizes new automation.

## Retained automation assets: historical fixes

`openSection` directly navigates to its destination URL rather than relying on a sidebar click that stalled in AliasMode Firefox. Dialog author visits ignore hidden links and navigate to the visible author's profile URL. The regression tests exercise these cases. Both soft and active preloaded scripts share these fixes; originals are reference-only.

## Historical automation log interpretation

`not logged in` is an early return and may still show a green succeeded badge. Check the selected tab and signed-in Home. A real completed run prints `done` and an actual-count summary. Counts can be below plan; topic results may include photos and unrelated accounts. Search visits add to queued profile visits. The original script's 'actions left over for another day' is a message, not persisted scheduling.

Script logs must be labeled as automation evidence, not manual completion confirmations. Reported restrictions/checkpoints pause runs; follow SOP.md and the user's official Instagram recovery instructions. Do not launch a routine to test whether a restriction cleared.

## Recovery

`docker compose restart desktop` restarts the app and desktop while preserving the named volume. Check logs first. Do not delete the volume as a recovery shortcut. Restarting may reopen the configured first profile; verify the intended profile before continuing.

For native AliasMode, a frozen import dialog was recovered by terminating only the identified desktop app and reopening it; its saved profiles survived. The fallback for installing scripts is a backed-up, atomic source-store update while AliasMode is closed, followed by reopening Scripts. The source store's schema is version-sensitive: inspect it and preserve IDs, timestamps, revisions, unrelated entries and edited source. Use tools/seed_scripts.py only to add missing entries.

## Native fallback

If containers cannot run the x64 browser, install official native AliasMode from https://aliasmode.com/docs/macos/ or https://aliasmode.com/docs/linux/ (Windows: official download page). Pin the documented supported release and verify checksums. The three `.mjs` files may be kept as private technical assets; create a Firefox profile and follow the same login and evidence-based automated workflow. This fallback is not fully containerized; state that accurately.
