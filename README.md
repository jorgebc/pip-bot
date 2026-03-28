# pip-bot — Personal Discord Bot

> > **Project name:** `pip-bot`

A personal, modular Discord bot running 24/7 on a Raspberry Pi 4.

---

## Table of Contents

1. [Project Philosophy](#1-project-philosophy)
2. [What the Bot Does](#2-what-the-bot-does)
3. [Environments](#3-environments)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Phase 1 Features](#6-phase-1-features)
7. [AI-Assisted Development — Prompt Roles](#7-ai-assisted-development--prompt-roles)
8. [Commit Convention](#8-commit-convention)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment on Raspberry Pi](#10-deployment-on-raspberry-pi)
11. [Services AI Layer — Action Dispatcher Protocol](#11-services-ai-layer--action-dispatcher-protocol)
12. [Roadmap](#12-roadmap)
13. [Contributing / Development Guidelines](#contributing--development-guidelines)

---

## 1. Project Philosophy

| Principle | Description |
|---|---|
| **Professional but pragmatic** | Clean architecture, separation of concerns, no over-engineering |
| **AI-assisted development** | Every step of the workflow is assisted by AI agents with clearly defined roles |
| **Modular by design** | Each feature is an independent cog; new capabilities are added without touching the core |
| **Prepared to scale** | The `services/ai/` layer is reserved from day one for future autonomous agents |
| **Private & personal** | Single Discord server, single owner, no multi-tenant requirements in Phase 1 |

---

## 2. What the Bot Does

Pip-bot is a **command executor** that runs 24/7 on a Raspberry Pi and exposes home infrastructure capabilities through Discord.

### Architectural model

```
External AI Agent (runs anywhere: PC, cloud, cron job...)
        │
        │  Discord message or slash command
        ▼
  pip-bot — running on Raspberry Pi
        │
        ├──▶ NAS (download torrent, list files)
        ├──▶ Email (send report)
        ├──▶ Local filesystem (save results)
        └──▶ Discord notification (reply with results)
```

**The bot contains no AI.** It is a reliable, always-on action layer. Intelligence lives in external agents that decide *what* to do; the bot handles *how* to do it on the local infrastructure.

**Discord is the communication bus.** Any process that can send a Discord message — a Python script, an AI agent, a scheduled task, or you typing manually — can trigger actions on the Raspberry Pi.

### Why this architecture

- The RPi has limited resources — no LLM inference on device
- Agents can run anywhere (your PC, a cloud function, a paid API) without requiring permanent uptime
- You interact with the system the same way regardless of whether the trigger is human or automated
- Adding a new agent means writing a new external script, not modifying the bot

---

## 3. Environments

### Development — PC

| Item | Details                                         |
|---|-------------------------------------------------|
| OS | Any (Windows/Linux/macOS)                       |
| IDE | IntelliJ IDEA (with Python plugin)              |
| AI in IDE | JetBrains AI Assistant or GitHub Copilot plugin |
| AI in CLI | Copilot cli                                     |
| Python | 3.11+                                           |
| Dependency manager | Poetry                                          |

### Production — Raspberry Pi

| Item | Details |
|---|---|
| Hardware | Raspberry Pi 4 Model B — 4 cores, 4 GB RAM |
| OS | Debian GNU/Linux 12 (Bookworm) — 64-bit |
| Kernel | `6.12.62+rpt-rpi-v8 aarch64` |
| Python | 3.11+ (verify with `python3 --version` on the RPi) |
| Dependency manager | Poetry (installed on RPi) |
| Process manager | `systemd` |
| Log management | `RotatingFileHandler` + `journalctl` |

> **Important — ARM64 compatibility:** always verify that all dependencies in `pyproject.toml` have ARM64 wheels available before adding them. Use `pip index versions <package>` or check PyPI for `linux_aarch64` wheel availability.

### Sync Strategy

```
PC (develop) → git push → GitHub → RPi (git pull + poetry install)
```

No direct file transfer. The Raspberry Pi always pulls from the canonical GitHub repository.

---

## 4. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Language | Python 3.11+ | Async support, extensive ecosystem, stable on aarch64 |
| Discord library | `discord.py` >=2.7.1 | Stable, well-documented, full slash command support |
| Dependency management | Poetry | Lockfile ensures identical environments on PC and RPi |
| Environment variables | `.env` + `python-dotenv` >=1.2.2 | Simple, secure, standard |
| Logging | Python `logging` stdlib + `RotatingFileHandler` | Professional from day one, no external dependencies |
| System monitoring | `psutil` >=7.2.2 | CPU, RAM, disk, uptime metrics |
| Version control | Git + GitHub | Standard; also serves as the deployment mechanism |
| CLI AI assistant | GitHub Copilot CLI | Integrated CLI agent with local context awareness |
| IDE AI assistant | JetBrains AI Assistant or GitHub Copilot | Integrated in IntelliJ, context-aware |
| Testing | `pytest` >=9.0.2 + `pytest-asyncio` >=1.3.0 | Industry standard for Python async testing |
| Code quality | `ruff` >=0.15.7 | Fast Python linter and formatter |
| Process management | `systemd` | Native on Raspberry Pi OS, robust, well-documented |

---

## 5. Project Structure

```
pip-bot/
├── bot/                    # Core bot: client setup, event loop, cog loader
│   ├── __init__.py
│   └── client.py           # Bot subclass, on_ready, global error handler
│
├── cogs/                   # Discord feature modules (one file per domain)
│   ├── __init__.py
│   ├── system.py           # /ping, /status, /uptime
│   ├── nas.py              # /nas status, /nas list, /nas download
│   └── notify.py           # Inbound message handler for external agents
│
├── services/               # Business logic, decoupled from Discord
│   ├── __init__.py
│   ├── nas/                # NAS interaction (Transmission RPC, filesystem)
│   │   └── client.py
│   ├── email/              # Email sending (smtplib or similar, 0 € cost)
│   │   └── client.py
│   └── actions/            # Action dispatcher — maps incoming commands to services
│       ├── __init__.py
│       ├── registry.py     # Maps action names to handler functions
│       └── handler.py      # Validates and executes an incoming action request
│
├── config/                 # Configuration loading and validation
│   ├── __init__.py
│   └── settings.py         # Reads .env, exposes typed Settings object
│
├── utils/                  # Shared utilities with no external dependencies
│   ├── __init__.py
│   └── logger.py           # Centralized logger factory
│
├── tests/                  # All tests — mirrors the source structure
│   ├── services/
│   └── utils/
│
├── scripts/                # Operational scripts, not part of the bot
│   ├── deploy.sh           # Pull + install + restart systemd service on RPi
│   └── setup_rpi.sh        # First-time setup on a fresh Raspberry Pi
│
├── .env.example
├── .env                    # NEVER committed
├── .gitignore
├── pyproject.toml
├── poetry.lock
├── pip-bot.service         # systemd unit file
├── CHANGELOG.md            # Updated on every merged PR
├── ROADMAP.md              # Phase-based project plan with completion criteria
└── README.md
```

### Key implementation details

**System service (`services/system.py`):**
- `SystemStatus` dataclass with fields: `uptime_seconds`, `cpu_percent`, `ram_percent`, `disk_percent`, `disk_used_gb`, `disk_total_gb`, `disk_free_gb`
- `get_system_status()` — synchronous (BLOCKING) version using `psutil`
- `get_system_status_async()` — async wrapper that runs blocking calls in executor thread pool
- `_format_timedelta()` — converts seconds to human-readable format (e.g., "5d 3h 42m")
- All functions include error handling and logging

**Base service abstraction (`services/base.py`):**
- Abstract `BaseService` class defining common interface for all services
- Methods: `initialize()`, `shutdown()`, `health_check()`, `get_status()`
- Supports future service implementations (NAS, email, etc.) in Phase 2+

**Phase 2–3 services (stubs only, not yet implemented):**
- `services/nas/client.py` — Transmission RPC client (placeholder)
- `services/email/client.py` — SMTP email client (placeholder)
- `services/actions/registry.py` — action name → handler function mapping (placeholder)
- `services/actions/handler.py` — validates and executes incoming actions (placeholder)

---

## 6. Phase 1 Features

These are the concrete commands the bot must implement in Phase 1. They serve as the development anchor — all architectural decisions are validated against these.

**Status: 3 of 5 commands implemented. NAS integration (commands 4–5) is Phase 2.**

### `/ping`
✅ **Implemented.** Responds with `Pong!` and current latency. Used to verify the bot is alive.

### `/status`
✅ **Implemented.** Returns a system health summary for the Raspberry Pi: CPU usage, RAM usage, disk usage, and system uptime. Uses Python's `psutil` library. Runs blocking psutil calls in a thread pool to avoid blocking the event loop.

### `/help`
✅ **Implemented.** Auto-generated command listing all available commands with a one-line description. Built using discord.py's built-in help system.

### `/nas status`
⏳ **Phase 2.** Returns the current state of the NAS: whether it is reachable on the local network, available disk space, and the number of active download tasks.

### `/nas list`
⏳ **Phase 2.** Lists the items currently available on the NAS, paginated (max 10 per page).

### `/nas download <magnet>`
⏳ **Phase 2.** Adds a download task to the NAS queue (via Transmission RPC or equivalent). The bot confirms the task was received or reports an error.

> **Note for AI agents:** command logic lives in `cogs/`. The actual interaction with external services (NAS, email, Discord API) lives in `services/`. Cogs only call service methods and format the response for Discord. See Section 5 for responsibility boundaries.

---

## 7. AI-Assisted Development — Guidance for Code Assistants

This project leverages AI assistants throughout the development workflow. Code assistants (IDE or CLI) should follow these guidelines:

### Key Principles

1. **Read the README and ROADMAP first** — understand the architecture and current phase before writing code
2. **Follow responsibility boundaries** — cogs stay thin; logic lives in services
3. **Test-driven development** — write tests alongside code; all services must be unit-tested
4. **Logging and error handling** — use `utils/logger.py`; never use bare `except`
5. **ARM64 compatibility** — check PyPI for `linux_aarch64` wheels before adding dependencies
6. **Documentation** — write Google-style docstrings; update CHANGELOG and ROADMAP on completion

### When Implementing a Feature

1. **Start with the service layer** — design the business logic in `services/` first
2. **Write tests** — use `pytest` and `pytest-asyncio`; mock all external I/O
3. **Then write the cog** — thin wrapper that calls the service and formats the response
4. **Document** — add Google-style docstrings and module-level comments
5. **Commit** — use Conventional Commits; include issue number if applicable

### Example Workflow for Phase 2 (NAS Integration)

```
1. Design `services/nas/client.py`:
   - Transmission RPC connection, status check, add download
   - Write tests in `tests/services/nas/test_client.py`
   
2. Implement `cogs/nas.py`:
   - `/nas status`, `/nas list`, `/nas download` commands
   - Call `services/nas.client` methods
   - Format responses as Discord embeds
   
3. Update documentation:
   - Update this README if NAS protocol details change
   - Update CHANGELOG under [Unreleased]
   - Update ROADMAP milestones
   
4. Commit with Conventional Commits:
   - `feat(nas): implement Transmission RPC client`
   - `feat(cogs): add /nas commands`
```

## 8. Commit Convention

This project uses **Conventional Commits** to keep history readable and enable automated changelogs.

```
<type>(<scope>): <short description>

[optional body]
[optional footer]
```

| Type | Use for |
|---|---|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `chore` | Maintenance (deps, config, CI) |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change with no behaviour change |
| `style` | Formatting, whitespace |
| `deploy` | Deployment scripts, systemd config |

**Examples:**
```
feat(nas): add /nas download command
fix(status): handle psutil permission error on RPi
chore(deps): upgrade discord.py to 2.4.0
docs(readme): add deploy section
test(services): add unit tests for nas client
deploy(rpi): add systemd service file and deploy script
```

> **For AI agents:** always generate commits following this format. The `scope` is optional but recommended — use the folder name (`bot`, `cogs`, `services`, `config`, `utils`).

---

## 9. Testing Strategy

### Framework

```
pytest
pytest-asyncio
```

### Scope

| Target | Approach |
|---|---|
| `services/` | Full unit tests — mock all external calls (HTTP, RPC, filesystem) |
| `utils/` | Full unit tests — pure functions, no mocking needed |
| `config/` | Unit tests — mock environment variables with `monkeypatch` |
| `cogs/` | **Not unit-tested directly** — cogs are thin wrappers; test the services they call |
| Integration | Manual testing against the real Discord server and NAS for Phase 1 |

### Conventions

- Test files mirror the source structure: `tests/services/nas/test_client.py` tests `services/nas/client.py`
- Each test file tests one module
- Use `@pytest.mark.asyncio` for all async test functions
- Mock external I/O at the boundary of `services/` — never let tests make real network calls

### Running tests

```bash
# All tests
poetry run pytest

# With coverage report
poetry run pytest --cov=. --cov-report=term-missing

# Single module
poetry run pytest tests/services/nas/
```

---

## 10. Deployment on Raspberry Pi

### First-time setup

```bash
# On the Raspberry Pi
git clone https://github.com/<your-username>/pip-bot.git
cd pip-bot
pip3 install poetry --user
poetry install --no-dev
cp .env.example .env
nano .env  # fill in DISCORD_TOKEN and other secrets
sudo cp pip-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pip-bot
sudo systemctl start pip-bot
```

### Updating after a push

```bash
# On the Raspberry Pi (or run via scripts/deploy.sh)
cd pip-bot
git pull origin main
poetry install --no-dev
sudo systemctl restart pip-bot
```

### systemd unit file (`pip-bot.service`)

```ini
[Unit]
Description=pip-bot Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pip-bot
ExecStart=/home/pi/.local/bin/poetry run python -m bot
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### Logging

- **Runtime logs:** `journalctl -u pip-bot -f` (live) or `journalctl -u pip-bot --since today`
- **Persistent file logs:** configured in `utils/logger.py` using `RotatingFileHandler`
  - Location: `logs/pip-bot.log`
  - Max file size: **5 MB**
  - Backup count: **3 files**
  - Total max log footprint: **~15 MB** (critical on SD card)
- `logs/` directory is in `.gitignore`

> **SD card warning:** uncontrolled logging is one of the main causes of SD card corruption on Raspberry Pi. The `RotatingFileHandler` limits are non-negotiable.

---

## 11. Services AI Layer — Action Dispatcher Protocol

This is the core integration point for Phase 2+. External agents communicate with pip-bot by sending structured messages to a **dedicated private Discord channel**. The bot listens on that channel, validates the message, and executes the requested action.

### Why a dedicated channel

- Separates automated commands from manual conversation
- Easy to audit: all agent requests are logged in one place
- Simple permission model: only you (and bots you authorise) can write to it

### Message protocol (Phase 2 — draft)

External agents send a JSON-formatted message to the actions channel:

```json
{
  "action": "nas.download",
  "params": {
    "magnet": "magnet:?xt=urn:btih:...",
    "title": "Title"
  },
  "agent": "search-agent",
  "request_id": "uuid-v4"
}
```

The bot responds in the same channel (or a results channel) with:

```json
{
  "request_id": "uuid-v4",
  "status": "ok",
  "message": "Download queued: Title"
}
```

### Action registry (`services/actions/registry.py`)

Maps action names to service handler functions. Adding a new capability means registering a new action — no changes to the core bot or cogs.

**Phase 2 planned actions:**
```
"nas.download"      → services.nas.client.add_download()
"nas.list"          → services.nas.client.list_files()
```

**Phase 3 planned actions:**
```
"email.send_report" → services.email.client.send()
```

### Security model (Phase 1–2 — simple)

- The actions channel is private: only you and explicitly authorised bots have write access
- The bot validates that the message author is on an allowlist defined in `.env`
- No cryptographic signing in Phase 1–2 — not needed for a single-owner private server

**Phase 3 enhancement:** may add HMAC signing for cloud-based agents

## 12. Roadmap

The full roadmap with phases, milestones, and completion criteria lives in [`ROADMAP.md`](./ROADMAP.md).

**Summary:**

| Phase | Goal | Status |
|---|---|---|
| 1 | Bot core + Raspberry Pi control | 🔄 In progress |
| 2 | NAS control + torrent downloads | ⏳ Pending |
| 3 | External agent protocol — Discord → Email bridge | ⏳ Pending |
| 4 | Movie Search Agent (external repo) | ⏳ Pending |
| 5 | Job Search + Rental Search agents | ⏳ Pending |

> Update `ROADMAP.md` when completing milestones. Update this table when closing a phase.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | ✅ Phase 1+ | — | Bot token from Discord Developer Portal |
| `DISCORD_GUILD_ID` | ✅ Phase 1+ | — | Your server ID (enables fast slash command registration) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `NAS_HOST` | ⏳ Phase 2 | — | Local IP of NAS (e.g., `192.168.1.100`); all NAS_* vars required together |
| `NAS_PORT` | ⏳ Phase 2 | — | Transmission RPC port (typically `9091`) |
| `NAS_USER` | ⏳ Phase 2 | — | Transmission username |
| `NAS_PASSWORD` | ⏳ Phase 2 | — | Transmission password |
| `ACTIONS_CHANNEL_ID` | ⏳ Phase 3 | — | Discord channel ID for agent commands; required for Phase 3+ |
| `ALLOWED_AGENT_IDS` | ⏳ Phase 3 | — | Comma-separated Discord user/bot IDs allowed to send actions |

**Notes:**
- Copy `.env.example` to `.env` and fill in required values
- **Never commit `.env` to Git** — it contains secrets
- NAS variables: if `NAS_HOST` is set, all four `NAS_*` variables must be set (enforced by `config/settings.py`)
- Phase 2–3 variables are optional in Phase 1; validation enforces that all-or-nothing rule for each section

**Current Phase 1 minimum:**
```bash
DISCORD_TOKEN=<your-bot-token>
DISCORD_GUILD_ID=<your-server-id>
```

---

## Contributing / Development Guidelines

This project is developed with strong AI assistance. When generating or modifying code:

1. **Read this README and ROADMAP first** — structure and conventions are non-negotiable
2. **Follow the phase workflow** — Phase 1 is core infrastructure (done); Phase 2 is NAS integration
3. **One responsibility per file** — if a file needs to import both `discord` and third-party HTTP libraries, it probably belongs in a service, not a cog
4. **All secrets via `.env`** — no hardcoded values anywhere; use `config/settings.py` for validation
5. **No bare `except`** — always catch specific exceptions and log them via `utils/logger.py`
6. **Logging over print** — use `utils/logger.py` to obtain a logger; never use `print()` in production code
7. **Async-first design** — use `asyncio` and `pytest-asyncio` for all I/O-bound operations
8. **ARM64 compatibility check** — before adding any dependency, confirm it has `linux_aarch64` wheels on PyPI
9. **Commit with Conventional Commits** format — see Section 8 for examples
10. **Update CHANGELOG.md on every PR** — add an entry under `[Unreleased]` describing what changed
11. **Update ROADMAP.md when completing a milestone** — check the box and document completion
12. **Version management:**
    - `PATCH` (0.1.x): bug fix or minor adjustment, no new functionality
    - `MINOR` (0.x.0): new functionality added — bump on every completed roadmap phase
    - `MAJOR` (x.0.0): breaking change to the external agent protocol or core architecture
    - Bump with: `poetry version patch` / `poetry version minor` / `poetry version major`
    - Always update version in the same commit that closes a phase PR

### Testing Checklist

Before submitting:
```bash
poetry run pytest                          # All tests pass
poetry run pytest --cov=. --cov-report=term-missing  # Coverage check
poetry run ruff check .                    # No linting errors
poetry run ruff format .                   # Code formatted
```

### New Dependencies

Before adding:
1. Check PyPI for `linux_aarch64` wheel availability
2. Update `pyproject.toml` with version constraints (e.g., `>=2.7.1,<3.0.0`)
3. Run `poetry lock` to update `poetry.lock`
4. Document in CHANGELOG under `[Unreleased]`