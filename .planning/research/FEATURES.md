# Feature Landscape

**Domain:** Telegram betting signal capture + analytics dashboard (virtual football / Bet365)
**Researched:** 2026-04-02
**Confidence:** HIGH for table stakes (well-established in comparable platforms), MEDIUM for differentiators (domain-specific to virtual football signal groups)

---

## Table Stakes

Features users expect from ANY betting analytics platform. Missing any of these and the tool feels broken or unfinished.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Signal capture in real time | Core value proposition — without this there is no product | Medium | Telethon NewMessage + MessageEdited events; already in architecture |
| Deduplication of signals | Without dedup, stats are wrong and trust is lost immediately | Low | ON CONFLICT upsert on message_id; already in schema |
| Result tracking (GREEN / RED) | Win rate is the first thing any bettor asks | Low | Requires edit detection to link result to original signal |
| Total signal count + win rate | Every bettor tracker shows this front and center | Low | COUNT(*), COUNT WHERE resultado = 'GREEN' / total |
| ROI simulation with fixed stake | "If I had bet R$10 on every signal, what would I have now?" — baseline question | Low | Stake * units_won - stake * units_lost; no odds = simplified model |
| Filter by liga (league) | Virtual football has multiple leagues; performance differs per league | Low | SQL WHERE liga = ? |
| Filter by entrada (bet type) | Different bet types (Ambas Marcam, Over/Under, etc.) have very different hit rates | Low | SQL WHERE entrada = ? |
| Signal history list | Bettors want to review individual signals; not just aggregates | Low | Paginated SELECT with filters |
| Pending signals (no result yet) | Signals without GREEN/RED pollute stats if not handled | Low | WHERE resultado IS NULL separate view |
| Startup terminal summary | Quick sanity check that the listener is running and data is flowing | Low | Print stats on `python listener.py` start |
| Data persists across restarts | Obvious expectation — losing history on restart destroys trust | Low | PostgreSQL persistence; already in architecture |

---

## Differentiators

Features that go beyond what generic bet trackers offer. These match the specific domain (virtual football signal group analysis) and create analytical edges for the user.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Win rate broken down by time of day (horario) | Virtual football runs on fixed RNG cycles; some practitioners claim time-of-day correlations exist — data either confirms or disproves this claim | Medium | GROUP BY horario; heatmap visualization recommended |
| Win rate broken down by day of week | Same hypothesis as time-of-day; weekly patterns from human tipper behavior may exist | Low | Use dia_semana column already in schema |
| Win rate broken down by periodo (1T / 2T / FT) | Half-time vs full-time bets may have fundamentally different hit rates for the same entrada | Low | GROUP BY periodo |
| Cross-dimensional analysis | "Ambas Marcam in World League on Friday evenings" — this compound filter reveals actionable patterns that single-dimension filters miss | High | Requires composable WHERE clauses across 4+ dimensions; most generic trackers only do one dimension |
| Equity curve chart | Shows cumulative bankroll over time with fixed stake — makes winning/losing streaks visible and emotionally tangible | Medium | Order signals by received_at; running sum of +stake or -stake |
| Streak tracking | Current win/loss streak and longest historical streak — helps identify hot/cold periods by league or entry type | Medium | Window functions in PostgreSQL or computed in Python |
| Gale analysis (1x / 2x coverage) | Signal groups often imply gale (martingale) recovery: "if RED, double next bet." Showing win rate at gale-1 vs gale-2 vs gale-3 level is a direct translation of how this audience actually bets | High | Requires consecutive signal grouping logic; needs schema to track sequence context |
| Signal volume chart by day / week | Shows whether the tipper is active and consistent; sparse days may correlate with worse performance | Low | COUNT signals GROUP BY DATE(received_at) |
| Parser coverage rate | % of messages that were successfully parsed vs dropped as unrecognized — operational quality metric | Low | Log parse failures; show in startup summary |
| Raw message viewer | View the original Telegram text alongside the parsed fields — essential for debugging parser regressions | Low | raw_text column already stored |

---

## Anti-Features

Things to explicitly NOT build in this project, with rationale.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Bet automation (Selenium / Playwright on Bet365) | High ban risk, high complexity, legally and technically fragile — explicitly out of scope in PROJECT.md | Use the dashboard to make decisions manually; automate only after 6+ months of validated data |
| Multiple Telegram group support | Requires multi-session Telethon management, schema changes, and UI routing complexity — scope creep with no clear user need right now | Hard-code the single group in config; add multi-group only if the user explicitly validates this need |
| Odds tracking | Bet365 virtual football signal messages do not include odds; adding odds would require scraping Bet365, which is high-risk | Use fixed-stake ROI as the default model; yield (ROI with odds) is a phase-2 concern if odds data becomes available |
| Kelly Criterion stake sizing | Requires reliable win probability estimates — which you are trying to DISCOVER with this tool, not assume | Stick to fixed-stake simulation; add Kelly only after a stable win rate baseline is established over hundreds of signals |
| Social / sharing features | This is a personal tool for one user — tipster public profiles, copy betting, social feeds add zero value and significant complexity | Keep auth-free localhost access; add auth only if multi-user is explicitly needed |
| Mobile app | Web-first is explicit in PROJECT.md; Chart.js + responsive layout covers the use case adequately | Ensure dashboard CSS is responsive; no native app needed |
| Predictive / AI scoring | Virtual football is RNG-based; machine learning on top of RNG data finds patterns in noise, not signal | Track descriptive statistics only; never imply predictions |
| Real-time push updates to browser | WebSockets for live signal arrival adds significant complexity (LISTEN/NOTIFY or polling loop) for marginal value — signals arrive infrequently | Add a manual "refresh" button or auto-refresh every 60s via meta refresh or lightweight JS polling |
| Multi-bankroll management | This is a single-strategy tool for one group — no need to track separate bankrolls | If the user adds a second strategy, this becomes relevant; not now |
| Result import from external sources | All results come from the edited Telegram messages; importing from external CSVs or sportsbook APIs adds fragile data reconciliation | Trust Telegram as single source of truth; no imports needed |

---

## Feature Dependencies

```
Signal capture (Telethon listener)
  └─ Parser (regex extraction)
       └─ Store (PostgreSQL upsert)
            ├─ Terminal summary stats  (reads DB on startup)
            └─ Dashboard API (FastAPI, read-only)
                 ├─ Signal history list  (paginated SELECT)
                 ├─ Aggregate stats (win rate, total, pending)
                 │    ├─ Filter: liga
                 │    ├─ Filter: entrada
                 │    ├─ Filter: periodo
                 │    └─ Filter: dia_semana / horario
                 ├─ ROI simulation with fixed stake
                 │    └─ Equity curve chart  (requires ordered signal history)
                 ├─ Win rate by dimension (requires GROUP BY queries)
                 │    └─ Cross-dimensional analysis  (requires composable filters)
                 └─ Streak tracking  (requires ordered signal history + window logic)

Gale analysis
  └─ Requires: consecutive signal grouping  (new schema consideration)
  └─ Depends on: signal history + parser identifying gale context in raw_text
```

---

## MVP Recommendation

The minimum product that delivers the core value ("are the signals actually profitable and what patterns exist?"):

**Prioritize for MVP:**

1. Signal capture + parse + store (listener pipeline) — the entire product depends on this
2. Terminal startup stats (total, greens, reds, win rate) — validates the pipeline is working before building UI
3. Dashboard: aggregate stats card (total, win rate, pending count)
4. Dashboard: filter by liga + filter by entrada
5. Dashboard: ROI simulation with fixed stake (simple running total)
6. Dashboard: signal history list (paginated, filterable)

**Add in v1.1 (after validating MVP with real data):**

- Equity curve chart (running bankroll over time)
- Win rate by horario (time-of-day heatmap)
- Win rate by dia_semana
- Win rate by periodo (1T / 2T / FT)
- Cross-dimensional filter (liga + entrada + periodo combined)

**Defer to phase 2:**

- Streak tracking: depends on having enough history to make streaks meaningful (100+ signals)
- Gale analysis: requires schema changes and signal sequencing logic; validate demand first
- Parser coverage rate display in dashboard: useful but low priority vs showing actual signal data

---

## Sources

- betr.pro platform features (Telegram bet integration, equity curves, P&L tracking): https://www.betr.pro
- Pikkit analytics features (cross-league performance, bet type filtering): https://pikkit.com/
- BettorEdge tracking practices: https://www.bettoredge.com/post/tracking-your-betting-performance
- greenvirtual.com.br features (virtual football time filters, gale analysis, league breakdown): https://greenvirtual.com.br/
- Bet365 virtual football pattern analysis — betcorrect.com: https://blog.betcorrect.com/2025/04/07/virtual-victory-advanced-statistics-and-patterns-in-virtual-sporting-games/
- HeatCheck HQ betting analytics overview 2026: https://heatcheckhq.io/blog/best-sports-betting-analytics-tools-2026
- Best bet tracking apps 2026: https://bvcompany.org/best-sports-betting-tracker-apps/
- Tipster analytics platform feature breakdown: https://ideausher.com/blog/tipster-analytics-platform-development/
- Smartbet.io analytics (ROI, drawdown, win rate per signal source): https://smartbet.io/
- BetGuru.ai signal transparency features: https://betguru.ai/
- Brazilian virtual football groups on Telegram: https://www.terrordasbets.com/post/grupos-futebol-virtual-telegram
- Kelly Criterion as advanced (not MVP) feature: https://en.wikipedia.org/wiki/Kelly_criterion
