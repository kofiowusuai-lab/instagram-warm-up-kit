# Instagram phone sessions

The user requested an adaptation of this existing kit to operate Instagram on their own phone using Phone Harness. Keep account record authority, warnings, UTC slots and private logs. Preserve legacy AliasMode accounts and the currently installed service; do not migrate or enable any real account automatically.

## Chosen approach

Add a local iPhone adapter and a bounded passive session runner. Select with `execution_backend: phone-harness`; absent means legacy AliasMode. This avoids rewriting scheduling and avoids Xcode/WebDriverAgent storage. Browser-only automation remains an optional alternative. Cloud phones are outside this request.

Require explicit account configuration, exact expected username, confirmed start date/timezone, approved routine and no unresolved warnings. A single global local-iPhone lock prevents overlapping accounts. The user selects the Instagram account; no automated switching. Calibrate two bottom navigation points against an actual screenshot (Profile and Reels), store normalized positions and window aspect ratio, recompute global points on every use. Refuse uncalibrated or changed layouts. Prove profile context using Posts/Followers/Following and the exact username in the top portion of the screen. Recheck identity each cycle before going to Reels. All input is passive; no liking, following, saving, commenting or DMs.

The runner forces local iOS, reads OCR after actions, stops on ambiguity, authentication, restrictions, disconnection, unchanged content after scroll or elapsed budget. Re-read authorization before every operation and during dwell. A warning-like feed string is recorded as possible warning, not a confirmed restriction. Persist pause immediately. No automatic recovery, checkpoint bypass or retry loops. Never infer watched Reels or completed engagement from a gesture; record observed screens, dwell and advances separately. Keep raw screen text and screenshots out of routine logs.

## Verification and rollout

Test with deterministic fake observations and time; test no device access when paused, identity mismatch, account lock, deadline and transport bounds, live pause, warning persistence and scheduler routing. Run existing tests too. Publish code and documentation after review. Local device pairing and a read-only preflight are separate from a live passive session, and must be labelled unvalidated until observed. Preserve unresolved warnings across backend changes.
