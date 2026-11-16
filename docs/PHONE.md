# Instagram on your own iPhone

The phone backend operates the real Instagram app through [Phone Harness](https://github.com/phone-harness/phone-harness) and Apple's iPhone Mirroring. It does not use Firefox, migrate cookies, sign in, change security settings or bypass verification. The Mac and iPhone must meet Apple's mirroring requirements. No Xcode, jailbreak, cloud phone or paid service is required. Phone Harness 0.3.3 is the integration version checked during development.

## What this version does

Passive Reels browsing on the account the user has selected. It checks the **own profile** username and owner controls, navigates using two explicitly calibrated bottom-bar points, and spends the configured dwell time only when visible OCR text matches one of the account's comma-separated `topic` phrases. It returns to the own-profile screen between iterations. It never likes, follows, saves, comments, sends messages or automatically switches accounts. Active phone mode is rejected even if an old browser account had active mode enabled.

This is not full browser-routine parity: no automatic niche search, profile discovery or Stories. The user selects the account and prepares its feed. Topic matching uses visible text only; unlabeled videos may be skipped, captions may be misread, and a topic match is not proof of relevance or playback. `max_items` limits iterations; `session_minutes` is an upper bound including navigation and startup, not guaranteed viewing time. The kit makes no guarantee about reach, account readiness or removal of restrictions.

## One-time setup

1. Install the published package in an isolated tool environment:

   ```bash
   uv tool install --python 3.12 'phone-harness==0.3.3'
   phone-harness --version
   phone-harness doctor ios
   command -v phone-harness
   ```

2. Open **iPhone Mirroring** on the Mac and complete Apple's pairing yourself. Keep the physical iPhone nearby and locked during control. The user handles all account credentials, device unlocks and verification.
3. Grant Accessibility and Screen Recording to the application named by the doctor if missing. Screen Recording may require restarting that application. Do not change protections to work around an Instagram restriction.
4. In the phone's Instagram app, select the intended account yourself and open **your own Profile tab**. Its username, Posts/Followers/Following and **Edit profile** must be readable in English. Starting on Home, Reels, a visited profile, DMs, a dialog or another language is deliberately unsupported until reviewed. The runner will refuse it rather than guess.

## Preserve account history

Use the same authoritative private directory for an existing account: its `SOP.md`, `progress.md`, `schedule.md`, `warnings.md` and `settings.json`, plus logs and scheduler state. Do not create a fresh history to escape a warning. An account may live outside this checkout; all commands accept an absolute `--account` path.

Before changing an existing browser account, disable `scheduler_enabled`, stop any current session, back up its records privately, and unload its old LaunchAgent. **An older scheduler can ignore `execution_backend` and still launch Firefox.** Install the new service only after its source path and live phone test are verified. The service label is based on the account-directory name, so reinstalling replaces that account's job; do not run old and new schedulers together. Leave other accounts and their skip dates unchanged. This integration does not modify existing services automatically.

New accounts can copy the five root templates into a directory under ignored `accounts/` without overwriting files. Fill in the confirmed label, timezone, start date and approved passive routine. Templates are not activity evidence.

## Calibration and private configuration

Calibration must come from the **actual current device screenshots**, not estimated coordinates or the example below. While preparing the session, manually inspect the Profile and Reels screens. Both must show a persistent bottom navigation bar and an unobstructed portrait layout. Locate the centres of Profile and Reels in their respective screens. For each screenshot, divide the centre's pixel x/y by the screenshot width/height. These normalized values are recomputed against current window bounds for each tap. Use the screenshot's width/height ratio as `aspect_ratio`. Refuse calibration if screenshots and the reported window bounds have a different aspect ratio. Retain raw screenshots only in private storage if needed for setup.

The bridge refuses a window aspect-ratio change greater than 3%. Equal-aspect UI changes still require operator recalibration; a simple aspect check cannot detect moved Instagram icons. Recalibrate after app navigation changes. Do not configure a bottom point on a send, compose, like or follow control. Never use an arbitrary screen tap to find a missing tab.

Merge these fields into the existing private settings; preserve all warning/history fields. Values below describe the schema, **not authorization or a ready-to-run account**:

```json
{
  "execution_backend": "phone-harness",
  "scheduler_enabled": false,
  "agent_engagement_enabled": false,
  "schedule_approved": false,
  "account_status": "awaiting_phone_setup",
  "phone": {
    "enabled": false,
    "platform": "ios",
    "mode": "soft",
    "expected_username": null,
    "harness_executable": null,
    "calibration": null,
    "dwell_seconds": 15,
    "max_items": 60
  }
}
```

Set `expected_username` to the actual handle without `@`, and `harness_executable` to the absolute path returned by `command -v phone-harness`. `calibration` is an object with `aspect_ratio` (number), `profile` ([normalized x, y]) and `reels` ([normalized x, y]); each point's y must be greater than 0.85. Set a nonempty comma-separated `topic` in root account settings. `dwell_seconds` is 5–60, `max_items` is 1–100, and the session budget is greater than zero and at most 20 minutes.

Only after user confirmation of the routine and warning status: set `phone.enabled`, `agent_engagement_enabled` and `schedule_approved` true; `active_mode_enabled` false; `account_status` to `ready_for_authorized_soft_runs`; and `reported_warning_status` to `none_reported` or `resolved` based on actual evidence. Record any resolution in warnings.md; never clear a known checkpoint just to pass validation. Confirm `timezone` and `warmup_start_date` too. **Keep `scheduler_enabled` false** for the first attended checks.

## Verify, then run

```bash
# Configuration only: no phone calls, no AliasMode calls.
python3 tools/phone_warmup.py --account accounts/YOUR-LABEL --check

# Connect/open Instagram and read own profile. No Reels browsing or scrolling.
python3 tools/phone_warmup.py --account accounts/YOUR-LABEL --preflight

# Attended passive session with the approved duration and iteration budget.
python3 tools/phone_warmup.py --account accounts/YOUR-LABEL
```

The preflight expects the user to have left the own-profile screen open; it does not navigate arbitrary screens to find it. Choose a short approved session budget initially. Inspect the actual result and private evidence JSON. A configuration check passing does not establish pairing or live success. Tests use synthetic OCR observations and fake time; no live Instagram run is implied by their success.

### Phone Harness 0.3.3 readiness compatibility

The kit also selects the main window by its localized application/title match,
rather than the first layer-zero window: macOS may put a 66×20 hover toolbar
ahead of the phone. Using that toolbar's bounds silently misdirects taps.
The scheduled bridge forces foreground input (`PHONE_HARNESS_BACKGROUND=0`),
activates before calculating calibrated points, and refuses taps when the main
window moved or another window covers the target. Target checks use the main
window ID, including when a covering window belongs to the same app.
The Mac's foreground window and pointer may change while a session runs.

OCR may merge the account/Reels dropdown arrow into its heading. The runner
accepts narrowly defined separated dropdown marks after the exact handle,
while still requiring owner controls. After a verified Reels navigation, three
distinct high-confidence numeric counters in the right rail can identify the
scrolled layout where Instagram hides the Reels heading. These checks are
layout-specific; an unsupported layout stops the run.

On the tested Mac, a live iPhone Mirroring window exposes native toolbar controls (`app.grid.3x3` and `iphone.app.switcher`). Upstream 0.3.3 can classify these as a disconnected screen. The kit loads `tools/mirroring_readiness.py` before every phone operation. It inspects the matched main window, accepts the observed stream hosting view or identified live toolbar, ignores only those two toolbar buttons and standard window chrome, and keeps native text, prompts, unknown controls, incomplete trees and accessibility failures blocked. Existing before/after-input guards stay active. Ordinary empty/chrome-only windows without the observed hosting view or live toolbar are not ready. This is a native structural check, not proof of video playback.

To apply the same compatibility to normal `phone-harness` script commands, register it in your **existing** agent workspace:

```bash
python3 tools/install_phone_compat.py --workspace ~/.phone-harness/agent-workspace
```

Use the actual workspace path if your install uses a different one (see Phone Harness's `PH_AGENT_WORKSPACE` and XDG rules). Registration preserves existing helpers, creates a private `.bak` rollback copy and refuses conflicting registrations. Keep this repository at its registered absolute path. The loader affects script commands; the upstream `phone-harness doctor ios` subcommand does not load agent helpers. A compatibility-aware diagnostic can run inside a script instead:

```bash
PHONE_HARNESS_PLATFORM=ios DO_NOT_TRACK=1 phone-harness <<'PY'
# task: Verify the local iPhone connection.
# step: Run diagnostics with the registered native-window compatibility.
from phone_harness.admin import run_doctor
raise SystemExit(run_doctor('ios'))
PY
```

This fix is pinned to Phone Harness **0.3.3** and refuses unvalidated versions. To undo the CLI registration, restore the installer-reported private backup to `agent_helpers.py`. Repository rollback also restores the prior bridge. Do not upgrade Phone Harness until the compatibility is revalidated, or restore the helper backup before upgrading.

## Scheduling and multiple accounts

The existing UTC scheduler dispatches the phone backend only when `execution_backend` is explicitly `phone-harness`. A missing backend preserves legacy AliasMode behavior; an unknown value is an error. The existing persisted skipped days and duplicate slot claims remain intact. After an attended successful phone test, record live validation and user schedule authorization before setting `scheduler_enabled` true and installing the service:

```bash
python3 tools/scheduler.py --account accounts/YOUR-LABEL --check
python3 tools/install_schedule.py --account accounts/YOUR-LABEL
```

Use one private account record per Instagram account, but only one physical-iPhone session can run at a time. A global OS lock at `~/.instagram-warmup/personal-iphone.lock` spans all account directories. A busy device records `device_busy`, not completed viewing. Select the desired Instagram account manually and leave its own Profile open before its slot. **This version cannot run unattended rotation across accounts.** A mismatched account is refused; it never switches accounts or takes over another run. If a deadline leaves the app on Reels, return to your own Profile before the next run.

The Mac must be awake, logged in, online and able to use the mirrored iPhone. Unlocking the phone interrupts mirroring. LaunchAgent execution has not been live-validated; permissions may differ from an interactive terminal. Do not claim headless operation or enable automatic sessions based on an installed plist alone.

## Stop conditions and records

Changing any account setting stops the next operation; disabling authorization or pausing status is checked before every operation and each second of dwell. Device operations have a timeout bounded by the remaining session budget. A timed-out operation is not retried; already delivered input cannot be undone. No auto-login, challenge solving, security-setting changes or cloud fallback occur. Every call explicitly forces the local iOS backend and disables optional telemetry.

Restriction/authentication-like OCR text stops the run and immediately persists a **possible warning**, disables engagement/scheduling and appends warnings.md. Feed captions can produce false alarms, so inspect before labelling a restriction confirmed. Detection is conservative English phrase matching, not exhaustive visual recognition; unsupported or ambiguous UI must be reviewed by the operator. An already-known unresolved warning blocks before any device call.

Results live under private `phone-runs/` with a progress.md evidence link. Logs contain outcome, elapsed dwell, observed screen changes and topic match counts; raw screen text, inbox content and screenshots are not written by the runner. Reel playback, other people's profile visits and Stories remain **unreported**. Likes/follows/saves/comments/DMs are explicit zero because the runner never attempts them. The repeated own-profile identity checks are not counted as other-profile engagement. Preserve weekly reports and warning history across backend changes.

## Rollback

Disable scheduling and unload the phone job first. Restore the private backed-up configuration and `execution_backend: aliasmode` only for an account that is still authorized and unrestricted; reinstall the original scheduler from its known path if desired. Do not delete phone/browser sessions or account records. Switching backend never resolves an Instagram restriction.
