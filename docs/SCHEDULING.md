# Fixed-GMT automated soft sessions

The scheduler operates without an LLM. It runs only the dedicated `ig-soft-timed-v1` passive script: no likes, follows, saves, comments or DMs. It uses the fixed navigation engine with a cooperative duration budget; an independent timer inside the script closes only its dedicated session tab at the limit. The scheduler never calls AliasMode's global Stop endpoint. Startup delays, failed login, restrictions or tool failures can shorten a session. Browser cleanup can take additional seconds. No claim is made that every minute is content playback.

## Account settings

In a private account's settings.json, retain the existing account fields and add:

```json
{
  "scheduler_enabled": true,
  "aliasmode_profile_id": "YOUR_EXISTING_PROFILE_ID",
  "aliasmode_helper": "/Applications/AliasMode.app/Contents/MacOS/aliasmode-mcp",
  "topic": "GTA 6, GTA VI, Grand Theft Auto VI, Rockstar Games",
  "schedule": {
    "timezone": "UTC",
    "times": ["07:00", "21:00"],
    "session_minutes": 20,
    "skip_days_per_week": 1
  }
}
```

Use your real profile ID; never create a second profile to obtain a fresh session. On Linux the helper is normally `/opt/aliasmode/bin/aliasmode-mcp` in this container. Verify the installed path; omit aliasmode_helper if the desktop is already managed by the container. Never paste a runtime nonce, cookie or browser endpoint into account settings.

**GMT is fixed UTC**, not Europe/London in summer. Therefore 07:00 GMT is 08:00 British Summer Time. One random whole day per week is the default; both sessions are skipped on that day. Skip dates are selected once and saved in scheduler-state.json. The first partial week samples only remaining dates. A preferred hour is not randomized to disguise activity.

## Install on macOS

Keep the account's five source files and settings in its private record directory, then:

```bash
python3 tools/scheduler.py --account accounts/YOUR-LABEL --check
python3 tools/install_schedule.py --account accounts/YOUR-LABEL
```

The read-only check verifies the pinned AliasMode runtime and reports configuration without launching Instagram. The installer creates a user LaunchAgent that ticks once per minute and after login. The tick compares UTC; it does not use local-hour calendar triggers. User must be logged in, with the machine awake and online. It does not change system power settings or wake the computer. An absent desktop can be started through the official helper.

`launchctl print gui/$(id -u)/local.instagram-warmup.YOUR-LABEL` shows job state. Disable the account by setting scheduler_enabled to false. Remove the service with `launchctl bootout gui/$(id -u)/local.instagram-warmup.YOUR-LABEL`; retain private records and profiles.

## Linux/container foreground service

Run `python3 tools/scheduler.py --account /data/manager/accounts/YOUR-LABEL --loop` under a user service or process supervisor. Start one process per account. Do not run both a host job and container job for the same profile. The repository does not automatically schedule every newly logged-in account. Existing image installations must rebuild to get the new code; account settings remain private in the volume.

## Failure and recordkeeping

There is a five-minute start grace period. Older slots are recorded as missed, not replayed. A per-account file lock and atomic prelaunch claim prevent duplicate runs, including after an uncertain crash. Failed starts are not retried in that slot. An unrelated AliasMode script blocks the session rather than being stopped. Warning pauses are persisted immediately as log chunks arrive. A runtime overrun disables future sessions instead of issuing a global stop. The adapter is pinned to beta.74 and fails closed if the version/source changes.

State and execution logs stay under the private account directory. Results append to progress.md with script-reported counts clearly labeled. Partial runs without a final counter summary remain unreported. Limits/challenges pause the account and disable scheduling; login failures also disable it until repaired. No bypass or timed automatic recovery is attempted.

The scheduling logic and duration-budget tests use simulated times; no additional 20-minute Instagram run is implied by passing those tests. Native operation uses the existing visible browser in the background. Headless operation has not been validated.
