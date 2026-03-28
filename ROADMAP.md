# pip-bot Roadmap

This roadmap reflects the intended evolution of the project in sequential phases.
Each phase builds on the previous one and has a clear, verifiable completion criterion.

**Current Status:** Phase 1 is ~90% complete. Core bot infrastructure is production-ready; NAS integration (Phase 2) is pending.

---

## Phase 1 — Bot Core & Raspberry Pi Control

**Goal:** the bot is running 24/7 on the RPi, reachable via Discord, and gives basic visibility and control over the system.

**Completion criterion:** I can open Discord from anywhere and check the health of my Raspberry Pi and restart the bot if needed.

### Milestones

- [x] `utils/logger.py` — rotating file logger factory
- [x] `config/settings.py` — typed settings loaded from `.env`
- [x] `bot/client.py` + `bot/__init__.py` — bot connects to Discord, logs on_ready
- [x] `cogs/system.py` — `/ping`, `/status` (CPU, RAM, disk, uptime)
- [x] `cogs/system.py` — `/help` auto-generated command list
- [x] `systemd` unit file — bot runs 24/7 on RPi, restarts on failure
- [x] `scripts/deploy.sh` — one-command deploy from PC to RPi via git pull
- [x] `scripts/setup_rpi.sh` — first-time RPi setup script

---

## Phase 2 — NAS Control & Torrent Downloads

**Goal:** the bot can interact with the NAS — check its status, browse available content, and queue torrent downloads — all from Discord.

**Completion criterion:** I can send a magnet link to the bot via Discord and the torrent starts downloading on the NAS.

### Milestones

- [ ] `services/nas/client.py` — Transmission RPC client (status, list, add download)
- [ ] `cogs/nas.py` — `/nas status`, `/nas list`, `/nas download <magnet>`
- [ ] Error handling for NAS unreachable (RPi offline, NAS offline)
- [ ] Unit tests for `services/nas/`
- [ ] `.env` variables for NAS connection documented and validated

---

## Phase 3 — External Agent Protocol: Discord → Email Bridge

**Goal:** the bot listens on a private Discord channel for messages from external agents. When an agent posts a finished report, the bot forwards it by email. The bot does not process or interpret the content — it is a bridge, nothing more.

**Completion criterion:** an external agent posts a report to the private Discord channel and I receive it in my inbox seconds later.

### How it works

```
Agent (cloud) — does its work, prepares the report
      │
      │  Discord message: { "action": "email.send_report", "subject": "...", "body": "..." }
      ▼
  pip-bot — receives message, validates sender, sends email
      │
      ▼
  My inbox
```

### Milestones

- [ ] `services/email/client.py` — email sending via SMTP (Gmail or similar, 0 €)
- [ ] `cogs/notify.py` — listens on private actions channel for incoming JSON messages
- [ ] `services/actions/registry.py` — action name → handler function mapping
- [ ] `services/actions/handler.py` — validates sender (allowlist) and dispatches action
- [ ] Supported actions in Phase 3: `email.send_report` only
- [ ] Unit tests for `services/actions/` and `services/email/`
- [ ] Protocol documented in README Section 11

---

## Phase 4 — First External Agent: Item Search

**Goal:** an autonomous AI agent (runs on cloud platform) searches for items matching my criteria, prepares a report, and sends it to pip-bot via Discord. The bot forwards the report by email. Optionally the agent can also trigger a torrent download.

**Completion criterion:** the agent runs on a schedule, finds matching items, and I receive the report in my inbox — optionally with the download already queued on the NAS.

### How it works

```
item-search-agent (cloud, scheduled)
      │  searches TMDB, filters by criteria, builds report
      │
      ├─▶ Discord: { "action": "email.send_report", "subject": "New items", "body": "..." }
      └─▶ Discord: { "action": "nas.download", "magnet": "...", "title": "..." }  ← optional
```

### Milestones

- [ ] New repo: `items-search-agent`
- [ ] Agent queries TMDB API (free tier) and filters by user-defined criteria
- [ ] Agent composes the report and posts it to the pip-bot actions channel
- [ ] Agent optionally sends `nas.download` action for automatic queuing
- [ ] Agent runs on a schedule (cron or cloud scheduler)

---

## Phase 5 — More Agents

**Goal:** expand the agent ecosystem with job and rental search agents that run autonomously and report results by email.

**Completion criterion:** I wake up with an email digest of new job listings and rental listings that match my criteria.

### Milestones

- [ ] New repo: `job-search-agent`
    - Scrapes/queries job listings by stack, location, salary
    - Sends `email.send_report` action to pip-bot with filtered results
    - Runs on daily schedule

- [ ] New repo: `rental-search-agent`
    - Scrapes/queries rental listings by location, price, size
    - Sends `email.send_report` action to pip-bot with filtered results
    - Runs on daily schedule

---

## Out of Scope (for now)

These ideas are noted but deliberately excluded to avoid scope creep:

- Smart home / home automation (lights, sensors) — possible Phase 6+
- Web dashboard for system monitoring — possible Phase 6+
- Persistent memory / conversation history — possible Phase 6+
- Multi-server or multi-user support — not needed, single private server

---

## Guiding Principles

- **One phase at a time** — do not start Phase 2 until Phase 1 is stable and deployed on the RPi
- **Each phase has a single completion criterion** — if it's not met, the phase is not done
- **External agents are independent repositories** — they are not part of pip-bot
- **Cost stays at 0 €** through Phase 3 — external API costs only appear in Phase 4+