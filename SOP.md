# Instagram Warm-up SOP

This is a manual activity planning and recordkeeping workflow. The agent prepares plans and records confirmations; the user performs Instagram activities. Bundled automation scripts are retained as reference/optional technical assets and are not executed by this manager.

## Initialize one account

Create a private directory using an account label such as `accounts/gta6-clips-01/`. In a container use `/data/manager/accounts/gta6-clips-01/` so records persist in the existing named volume. Do not put credentials or session data in records.

Copy the repository's `SOP.md`, `progress.md`, `schedule.md`, `warnings.md` and `settings.json` there only if absent; create `daily-logs/` and `weekly-reports/`. Do not overwrite an existing account's files. The selected directory's five files become its source of truth. Record its account label, timezone and agreed start date in settings only after confirmation. Do not populate historical activity from assumptions or convert automated test logs into manual completion records.

For a host installation, for example:

```bash
mkdir -p accounts/gta6-clips-01/daily-logs accounts/gta6-clips-01/weekly-reports
# Copy each starter file only when it does not already exist.
```

An agent operating inside the container can access root starters at `/opt/kit/` and the persistent record directory at `/data/manager/accounts/`. Agents without container tools can keep the private host record directory instead. Do not maintain two divergent copies for the same account.

## Plan each day

Read all five account files. Require confirmed timezone/start date and an approved schedule before describing a plan as scheduled. Day 1 is the confirmed start date; warm-up day is calendar days since that date plus one in the chosen timezone. Week is `floor((day - 1) / 7) + 1`. For a future start date, status is not started. Pauses and skipped days do not silently reset or advance the calendar; any change in start date/schedule requires explicit agreement and a recorded reason.

The repository does not prescribe evidence-free action quotas or escalation targets. Ask for the user's intended routine and constraints, draft schedule.md, and obtain approval. Keep planned and completed values separate. Reuse today's log if one exists to avoid duplicate plans or double counting. Show the checklist and wait for approval, then wait for the user to perform it manually.

## Record completion

Ask for actual counts for every tracked activity, minutes spent, completion/partial/skip status and any warnings. If the user gives only partial results, save those confirmed fields and keep all other fields unreported. Confirm ambiguous totals rather than guessing. An absence of a warning report is unknown; 'none reported' requires the user to say so.

Save `daily-logs/YYYY-MM-DD.md` using docs/DAILY-LOG-TEMPLATE.md. Record the confirmation source as a dated user report, not a credential or private message transcript. Update progress.md totals from the daily logs; do not add totals cumulatively a second time when revising the same day. Retain correction history when the user amends a report.

## Warnings and pauses

Record exact user-reported warning wording or a faithful summary, reported date, affected account, current status and any recovery action the user reports. Mark restrictions/checkpoints as paused in settings/progress and recommend no further engagement. Direct the user to the official instructions displayed by Instagram. Do not work around restrictions, invent recovery timeframes, or resume solely because time has passed. Record the user's update on resolution and approval of a revised plan before resuming recommendations.

## Weekly review

For each seven-calendar-day period anchored to the confirmed start date, save a report using docs/WEEKLY-REPORT-TEMPLATE.md. Compare confirmed actual activity to approved plans; list unreported days and confirmed skips separately. Review warnings and propose next week's checklist for approval. Never mark a draft as approved or infer missing activity.

## Report and privacy

Use the AGENTS.md daily report format regardless of provider. Store only noncredential account labels and operational records. Keep personal account records outside Git, protect backups, and preserve the existing Docker volume. Conversation context can help clarify a record but does not replace it.
