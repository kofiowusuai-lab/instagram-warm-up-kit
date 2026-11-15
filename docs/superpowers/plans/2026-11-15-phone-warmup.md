# Instagram Phone Warm-up Implementation Plan

**Goal:** Run bounded passive Instagram sessions on the user's own mirrored iPhone, preserving the existing manager and browser backend.
**Architecture:** Standalone standard-library runner, subprocess Phone Harness adapter, global device lock, opt-in scheduler dispatch. Account-specific calibration avoids guessed icon taps. Existing source-of-truth records remain private.
**Tech stack:** Python 3, Phone Harness 0.3.3, macOS iPhone Mirroring, unittest.

1. Add `tests/test_phone_warmup.py` first: authorization, exact top-profile username, global contention, local backend routing, dynamic bounds, timeouts, warning persistence, record evidence, live pause and deadlines. Run tests and observe missing implementation failures.
2. Add `tools/phone_harness_client.py` with a fixed allowlisted command bridge (no arbitrary account-supplied scripts), bounded calls, no telemetry, local iOS forced, sanitized errors. No credentials or raw screens in logs.
3. Add `tools/phone_warmup.py`: read five account files, validate configuration, global device lock, read-only inspection, opt-in passive session, immediate warning pause, atomic result records and progress links. Calibrated Profile/Reels navigation only. Limits before every operation and inside waits.
4. Test scheduler dispatch before modifying `tools/scheduler.py`; select backend explicitly, reject unknown providers, retain existing slot semantics, report phone readiness without browser access.
5. Document setup/calibration/migration and update blank settings/AGENTS/SOP. Do not copy private records into Git or enable a real schedule.
6. Run Python, Node, syntax and Compose checks. Review through independent reviewer, fix findings, push feature branch and PR. Check CI; retain live verification limitation when pairing is unavailable.
