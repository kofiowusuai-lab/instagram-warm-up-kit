# Instagram AliasMode Kit

A portable AliasMode desktop with **soft and active Instagram scripts preloaded**, persistent browser profiles, and instructions an AI agent can follow.

## Quick start

Install [Docker Desktop](https://docs.docker.com/get-started/get-docker/) on Mac/Windows, or Docker Engine with Compose on Linux. Start Docker, then:

```bash
git clone https://github.com/kofiowusuai-lab/instagram-aliasmode-kit.git
cd instagram-aliasmode-kit
./setup.sh
```

Windows: run these commands in WSL2 with Docker Desktop's WSL integration enabled. Alternatively run `docker compose up -d --build` in PowerShell from the cloned folder; `.env` is optional.

Open **http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=remote**. The first build downloads the desktop libraries and the pinned AliasMode release (several hundred MB). No host AliasMode, Node, Python, browser engine, proxy subscription, or AliasMode Cloud account is required.

1. Fresh installations are configured in **Local mode** automatically. The startup task creates `Instagram-Clips-01` and opens Instagram. If that task timed out during onboarding, run `docker compose exec desktop python3 tools/bootstrap_profile.py`.
2. Create your Instagram account or sign in inside that browser. Complete verification yourself.
3. Give your agent the account label, timezone, intended routine and start date. It creates a private account record directory from the five starter files: `SOP.md`, `progress.md`, `schedule.md`, `warnings.md`, and `settings.json`.
4. Ask **“Start today's warm-up.”** The agent reads those files, checks warnings, and runs the authorized script mode, recording actual output.
5. The agent saves the execution log, reports actual counts/outcome, updates progress and warnings, and produces weekly reviews. Report any additional manual activity separately.

**Automated activity is the default workflow.** Soft mode is the tested passive default. Active mode performs likes/follows/saves and requires explicit mode selection or a recorded approved schedule. No recurring scheduler is installed by this repository; a preferred time window alone does not enable one.

## Give this to your agent

> Clone this repo and follow AGENTS.md and SOP.md. Set up the container and profile for [NICHE], handle installation and routine recovery, and let me sign in and complete verification. Initialize private per-account records, then run the approved soft mode and record actual execution results. Keep warnings and weekly reports. Do not switch to active mode or claim a recurring schedule exists without the corresponding recorded configuration.

This manager is provider independent: Codex, OpenCode, Claude Code or another agent can follow the same Markdown records. If MCP is unavailable, manual user input and local files are sufficient. The agent should read [AGENTS.md](AGENTS.md), [SOP.md](SOP.md) and [the installation workflow](docs/WORKFLOW.md).

For each additional account, create a separate browser profile and private record directory. Host records belong under ignored `accounts/<label>/`; container records belong under `/data/manager/accounts/<label>/`, in the persistent volume. Keep the root starter documents blank, and do not commit private activity records.

## What is included

| Item | Behavior |
|---|---|
| `ig-soft-warmup` | Passive automated activity; plans zero likes/follows/saves |
| `ig-active-warmup` | Active automated activity with likes/follows/saves; explicitly selected mode |
| `ig-soft-smoke-test` | Same fixed engine, 3 planned items and 1 queued profile visit, 5-second feed scroll |
| `scripts/original/` | Reference copies reconstructed from the supplied scripts; not preloaded |
| `tools/seed_scripts.py` | Adds missing private script copies without overwriting existing edits |
| `tools/bootstrap_profile.py` | Creates/reuses the initial profile, opens Instagram, never handles credentials |

The two observed navigation fixes are included in all preloaded scripts: direct section navigation and visible-author profile navigation. The active plan is bundled but **has not been validated live**. The fixed soft engine passed a short macOS live test; a complete production session and this Linux container have separate validation status in [VALIDATION.md](docs/VALIDATION.md).

These routines automate browsing, not a measurable account 'warmth'. They do not guarantee reach or removal of restrictions. Search results can be unrelated, photo posts can be counted as reels, and actual totals may fall below the plan. There is no cross-run daily cap or account-readiness tracking.

## Change the niche

Record the niche and approved automated mode in account settings/schedule. Soft has zero saves; active plans a save on 30% of runs. Neither starts saving on Day 4 or automatically switches mode.

Before the first start, copy `.env.example` to `.env` and change `TOPIC` and `PROFILE_NAME`. Or supply `topic` JSON on each run, which is best for accounts in different niches. Existing saved scripts are preserved on restart, so later `.env` changes do not replace their defaults. Use run inputs or edit the private copy in AliasMode.

The sample niche is GTA 6. Standalone `Vice City` was removed because it returned unrelated businesses. Use a few specific related phrases rather than broad keywords.

## Start, stop and maintain

```bash
docker compose up -d             # start existing installation
docker compose stop             # stop; retain accounts and sessions
docker compose restart desktop  # recover a stuck desktop
docker compose logs --tail=100 desktop
docker compose exec desktop cat /tmp/bootstrap-error.log
```

Accounts, cookies, settings and saved script edits live in the named Docker volume `aliasmode-data`. Keep that volume private and back it up as sensitive session data. `docker compose down` preserves it; **`docker compose down -v` deletes it**. Never upload the volume, credentials, cookies, `.env`, or logs containing session endpoints to GitHub.

Only the desktop port is published, on **127.0.0.1**. The AliasMode API, CDP endpoints and VNC backend remain inside the container. Do not change the published address to `0.0.0.0` or expose it publicly. On a remote server use an SSH tunnel: `ssh -L 6080:127.0.0.1:6080 user@server`.

AliasMode's Linux distribution is **x86_64 only**. Compose requests `linux/amd64`; Apple Silicon/ARM container execution is not supported by this tested release: the sidecar failed under local ARM emulation. Use native AliasMode there, or run this container on an x64 host. The image runs as an ordinary user and does not request privileged mode or disable browser sandboxes. If the host blocks required browser facilities, use a supported x64 Linux host or native AliasMode; do not silently bypass sandbox protections.

Updates preserve private scripts by design. See [UPGRADING.md](docs/UPGRADING.md) for intentional source updates and verification.

## Provenance

Browser platform: [AliasMode](https://github.com/aliasmode/aliasmode), pinned to `0.1.0-beta.74`, downloaded from its official GitHub release and checked against a pinned SHA-256. Official [Linux requirements](https://aliasmode.com/docs/linux/), [scripts](https://aliasmode.com/docs/scripts/), and [Local API](https://aliasmode.com/docs/local-api/).

Warm-up scripts were supplied by the repository owner from Denis Hampl's material and adapted here with the documented fixes. They are not assigned an open-source license by this repository. Preserve attribution and confirm redistribution rights before making this private kit public. Third-party applications retain their own licenses; no Instagram or Rockstar affiliation is implied.
