# 7-day execution plan (with checklist)

## Day 1 - Planning (everyone, together)
- [ ] Read `docs/ARCHITECTURE.md` as a group; argue about at least one decision
- [ ] Walk through this repo: run seed, start backend, run tests
- [ ] Confirm/rewrite the API contract (`docs/API_CONTRACT.md`)
- [ ] Repo setup: protect `main`, branch naming (`feat/...`, `fix/...`), PR template, `.gitignore` check
- [ ] Each person runs the stack locally. Exit: "hello world" on every machine

## Days 2-3 - Parallel build
- [ ] A: rewrite `scheduler.py` from scratch, then diff against the reference
- [ ] B: rewrite `routers/` + `schemas.py`; add ONE endpoint of your own (e.g. bulk pause)
- [ ] C: extend the data model with one field (e.g. `description`) end-to-end: model -> schema -> form -> migration-by-hand
- [ ] D: rebuild UI with `VITE_USE_MOCK=true` first, then wire to the real API
- [ ] E: CI on every PR; write 3 more tests (suggestions: interval boundary at exactly 10s; PATCH invalid cron; pause mid-retry-sequence)
- [ ] Standup 15 min daily. Rule: if you wait >2h on someone, build against mocks

## Day 4 - Integration & feature freeze
- [ ] Frontend wired to real API end-to-end
- [ ] Scheduler runs against the real DB
- [ ] Fix CORS/timezone/serialization bugs (expect them)
- [ ] **No new features after today** - v2 ideas go in README

## Day 5 - Testing & security
- [ ] Full suite green in CI
- [ ] Failure-path demo rehearsed (500 -> retry -> exhausted)
- [ ] Secret scan: `git log -p | grep -i -E "key|token|password"` returns nothing
- [ ] Deploy to staging (Render + Vercel + Supabase); demo script timed

## Day 6 - Deploy & docs
- [ ] Production deploy works with seeded data
- [ ] README complete: setup, env vars, architecture, limitations, v2
- [ ] Record 2-min backup video
- [ ] `AI_USAGE.md` filled in honestly

## Day 7 - Demo & retrospective
- [ ] Rehearse `docs/DEMO_SCRIPT.md` twice
- [ ] Each person can state their component + one decision in <60s
- [ ] Present; run retro (went well / badly / would change)
