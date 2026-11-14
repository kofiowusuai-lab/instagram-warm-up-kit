# Validation status

## Known live evidence

On 2026-11-14, AliasMode 0.1.0-beta.74 on macOS Firefox, the fixed soft engine completed a short test through Home, notifications, inbox, feed, search, profile visits, topic items, normal Reels feed and return Home. Actual summary: 2 counted topic items, 3 profile visits, zero likes/follows/saves/stories. It skipped 16 nonmatching feed items. This was a short test, not a completed full-length production routine.

The active plan is supplied and preloaded but has not been validated live. Do not infer that browser UI actions in active mode work merely because passive browsing passed. Linux/container verification is recorded separately below.

## Automated checks

Five Node regression cases cover direct section navigation and hidden-author handling. Six Python cases cover script seeding without overwriting edits/corrupt stores, profile reuse, explicit Firefox creation without credentials, and paginated profile discovery. These use narrow test doubles and do not simulate Instagram end to end.

The container must be built and its desktop/app startup checked independently. A graphical startup test does not establish that login, every Instagram DOM selector, or active actions work on every machine.
