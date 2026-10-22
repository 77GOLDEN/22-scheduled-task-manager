# 5-minute demo script

Before the demo: reseed (`python seed.py`), start backend + frontend,
open the dashboard in two tabs (one zoomed for the audience).

| Time | Who | What |
|---|---|---|
| 0:00-0:30 | E | Intro: what it does, who built what (roles slide). Show seeded dashboard with countdowns. |
| 0:30-1:30 | D | Create a task LIVE: "always-fails, every 60s, max retries 2". Point out server-side validation feedback in the form. |
| 1:30-3:00 | A | The money shot: watch the Flaky task execute -> attempt 1 `failed` -> retry `queued` with backoff -> attempt 2 -> `exhausted`. Explain the status lifecycle on screen. |
| 3:00-4:00 | B + C | Quick pass: data model (Task vs Execution), validation rules, `/docs` page. Show one 422 by submitting a bad cron. |
| 4:00-5:00 | E | Tests: run `pytest` live (13 tests). Then limitations + v2. Close with "smaller, complete, tested". |

## Talking points per person (one technical decision each)
- **A (scheduler):** "Why polling instead of cron triggers" (see ARCHITECTURE #1)
- **B (API):** "Why validation lives in Pydantic schemas, not the router"
- **C (persistence):** "Why executions are rows, not a counter" (ARCHITECTURE #7)
- **D (UI):** "Why 30s polling beats WebSockets for this MVP"
- **E (QA/DevOps):** "Why the scheduler's tick is a separate, directly testable function"

## If live demo fails
Play the recorded walkthrough video, then show the deployed URL and the
test run. Judges reward a calm fallback.
