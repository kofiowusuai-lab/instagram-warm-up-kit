# Scheduled soft sessions implementation plan

Goal: run the authorized account at 07:00 and 21:00 fixed GMT, targeting 20 minutes, with one persisted random skipped day per week by default.

Architecture: a dependency-free Python tick runner checks UTC slots and persistent per-account state. macOS launchd invokes it once per minute. A version-checked AliasMode loopback client submits a dedicated timed soft script through the pinned desktop's authenticated Scripts API. Existing scripts remain unchanged. A cooperative duration budget plus a dedicated-tab close timer bounds sessions without using the global Stop endpoint. No model is needed for execution.

- [x] Add tests for fixed UTC times, grace window, persisted skipped dates, no duplicate slots, paused accounts and active-run ownership. Run failing cases before implementation.
- [x] Add a narrow pinned-version authenticated AliasMode Scripts client. Keep descriptor nonce and endpoints out of logs. Verify health generation and refuse concurrent unrelated runs.
- [x] Derive a timed passive variant from the fixed soft engine. Test its budget handling and preserve challenge stops; never enable active engagement.
- [x] Implement per-account lock, atomic claims/results, missed-slot reporting, log capture and pause on warnings. Never retry uncertain starts or synthesize counts for interrupted work.
- [x] Add a portable foreground scheduler loop and macOS installer using a UTC tick rather than local-hour triggers. Verify the installed launchd job and perform a non-engagement health/self-check.
- [x] Document installation, skip cadence, GMT versus BST, wake requirements, no catch-up, and actual execution limitations. Update private account configuration, run checks, commit and push source without private records.

A visible browser is the supported native execution path. Do not claim headless operation was verified. No extra live Instagram session is needed to test scheduling logic.
