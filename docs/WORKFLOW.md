# Operating workflow

## First installation

Use the README quick start. The container stores AliasMode at `/opt/aliasmode`, the kit at `/opt/kit`, and account state under `/data`. Scripts are seeded before AliasMode starts into `/data/com.aliasmode.desktop/custom-scripts/local.json`. Existing copies are never overwritten. Fresh installations also receive a Local-mode config before app startup; existing configs are preserved. Bootstrap uses only the documented loopback status/profile/browser routes; it explicitly creates Firefox rather than the API's Chromium default. It reuses a matching profile name and handles list pagination.

If AliasMode displays welcome/local-mode onboarding, complete it in the desktop. If the initial-profile task timed out, rerun `docker compose exec desktop python3 tools/bootstrap_profile.py`. It never handles Instagram credentials. Check the actual browser window and navigate to Instagram manually if browser launch arguments are ignored by a future platform release.

## Adding accounts

Create a separate named AliasMode profile, open Instagram there, and let the owner sign in. Keep a simple local record of profile name, niche, last run, and result, without credentials. Select the intended profile only. Use topic input JSON rather than modifying the shared script per account. Test one profile before batch use. Let machine capacity determine concurrency; concurrency does not establish account safety.

## Two preserved fixes

`openSection` directly navigates to its destination URL rather than relying on a sidebar click that stalled in AliasMode Firefox. Dialog author visits ignore hidden links and navigate to the visible author's profile URL. The regression tests exercise these cases. Both soft and active preloaded scripts share these fixes; originals are reference-only.

## Reading results

`not logged in` is an early return and may still show a green succeeded badge. Check the selected tab and signed-in Home. A real completed run prints `done` and an actual-count summary. Counts can be below plan; topic results may include photos and unrelated accounts. Search visits add to queued profile visits. The original script's 'actions left over for another day' is a message, not persisted scheduling.

No stories is normal for a new account. A challenge or limit is a stop condition, not a technical retry. An unhandled timeout is a software failure: inspect logs and debug it before another session. Avoid repeated full runs while debugging.

## Recovery

`docker compose restart desktop` restarts the app and desktop while preserving the named volume. Check logs first. Do not delete the volume as a recovery shortcut. Restarting may reopen the configured first profile; verify the intended profile before continuing.

For native AliasMode, a frozen import dialog was recovered by terminating only the identified desktop app and reopening it; its saved profiles survived. The fallback for installing scripts is a backed-up, atomic source-store update while AliasMode is closed, followed by reopening Scripts. The source store's schema is version-sensitive: inspect it and preserve IDs, timestamps, revisions, unrelated entries and edited source. Use tools/seed_scripts.py only to add missing entries.

## Native fallback

If containers cannot run the x64 browser, install official native AliasMode from https://aliasmode.com/docs/macos/ or https://aliasmode.com/docs/linux/ (Windows: official download page). Pin the documented supported release and verify checksums. Import the three `.mjs` files under `scripts/` into private scripts and create a Firefox profile. All later login/topic/testing steps are the same. This fallback is not fully containerized; state that accurately.
