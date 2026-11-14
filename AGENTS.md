# Instructions for installation agents

The user's goal is an easy, repeatable setup. Read README.md and docs/WORKFLOW.md, then carry out the authorized setup rather than only returning commands.

1. Check OS/architecture, Git and a working Docker + Compose installation. Install missing prerequisites from official sources within user authorization. Do not claim a stopped daemon or unsupported ARM emulation is working. On Windows use WSL2 + Docker Desktop. On a native-only host follow docs/WORKFLOW.md's fallback.
2. Inspect existing containers/volumes/profile names first. Preserve all existing account state. Copy `.env.example` only if `.env` is absent. Set the user's niche and profile name; do not invent unrelated brand requirements.
3. Run `./setup.sh` or `docker compose up -d --build`. Open the localhost noVNC URL. Use approved UI tools for UI operations, connector APIs where supported. Do not expose browser-control APIs or publish session endpoints.
4. Confirm the graphical desktop and AliasMode load. Finish ordinary local-mode onboarding. The bootstrap task creates/reuses the initial Firefox profile; inspect its log and retry it after onboarding if needed. Verify the selected account profile and the three preloaded scripts. Do not create duplicate profiles just because a command timed out.
5. Hand over only for new Instagram credentials, signup terms/verification and any actions requiring user participation under the active tool policy. Do not ask the user to restart apps or fix things you can repair. Recover the container/app yourself when routine recovery is authorized; preserve the volume.
6. After login, put the script-selected Instagram tab on Home. The runner may use the first tab, including an older password-reset tab, rather than the tab visible to the user. Do not assume a 'not logged in' message means the session itself is absent.
7. Run local checks, then the soft smoke test on one profile, concurrency 1, correct topic input, saved credentials access off. Check complete logs. A successful runner exit alone is not sufficient. Stop on Instagram limits/challenges; do not work around them or keep retrying.
8. Report actual counts and failures. Run one full soft session only when authorized. Never silently choose the active script; it performs real likes/follows/saves. Do not claim an account is warmed, guaranteed unrestricted, or that the active script was tested merely because soft passed.
9. For additional accounts create one new persistent profile each, use per-run topic inputs, repeat short validation, and preserve all earlier state. No automatic daily scheduler or global daily action cap exists. Do not run repeated sessions as though those controls exist.
10. If a new UI failure occurs, capture the error, use a focused regression test, change the smallest supported piece, and validate one account before broader use. Do not replace the corrected script with an older public-library copy.

Checks: `python3 -m unittest discover -s tests -v`, `node --test tests/*.test.mjs`, `find scripts -name '*.mjs' -exec node --check {} \;`, and `docker compose config --quiet`. Node is only needed for host tests; runtime Node is bundled with AliasMode.

Keep code changes and verification evidence in Git, never account cookies, passwords, inbox contents, volume exports, private CDP URLs or user-specific profile databases. Keep the repository private unless the owner explicitly authorizes public visibility.
