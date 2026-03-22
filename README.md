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
11. [Services AI Layer — Minimum Contract](#11-services-ai-layer--minimum-contract)
12. [Roadmap](#12-roadmap)

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
        ├──▶ NAS (interact with local NAS via HTTP/RPC)
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

| Item | Details |
|---|---|
| OS | Any (Windows/Linux/macOS) |
| IDE | IntelliJ IDEA (with Python plugin) |
| AI in IDE | JetBrains AI Assistant or GitHub Copilot plugin |
| AI in CLI | Aider (`pip install aider-chat`) |
| Python | 3.11+ |
| Dependency manager | Poetry |

### Production — Raspberry Pi

| Item | Details                                            |
|---|----------------------------------------------------|
| Hardware | Raspberry Pi 4 Model B — 4 cores, 2 GB RAM         |
| OS | Debian GNU/Linux 12 (Bookworm) — 64-bit            |
| Kernel | `6.12.62+rpt-rpi-v8 aarch64`                       |
| Python | 3.11+ (verify with `python3 --version` on the RPi) |
| Dependency manager | Poetry (installed on RPi)                          |
| Process manager | `systemd`                                          |
| Log management | `RotatingFileHandler` + `journalctl`               |

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
| Discord library | `discord.py` 2.x | Stable, well-documented, full slash command support |
| Dependency management | Poetry | Lockfile ensures identical environments on PC and RPi |
| Environment variables | `.env` + `python-dotenv` | Simple, secure, standard |
| Logging | Python `logging` stdlib + `RotatingFileHandler` | Professional from day one, no external dependencies |
| Version control | Git + GitHub | Standard; also serves as the deployment mechanism |
| CLI AI assistant | Aider | Open-source, works with Claude/GPT API or local models |
| IDE AI assistant | JetBrains AI Assistant | Integrated in IntelliJ, context-aware |
| Testing | `pytest` + `pytest-asyncio` | Industry standard for Python async testing |
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
├── pip-bot.service           # systemd unit file
└── README.md
```

### Responsibility boundaries

| Folder | Contains | Does NOT contain |
|---|---|---|
| `bot/` | Discord client setup, event hooks, cog loader | Business logic, external API calls |
| `cogs/` | Discord command definitions, user-facing responses | Logic beyond formatting and calling services |
| `services/nas/` | Transmission RPC client, filesystem queries | Discord objects |
| `services/email/` | Email composition and sending | Discord objects |
| `services/actions/` | Action registry and dispatcher for external agent commands | Discord objects, business logic |
| `config/` | Env loading, type-safe settings | Default values that belong in `.env.example` |
| `utils/` | Pure, stateless helper functions | Anything with side effects or external I/O |
| `tests/` | `pytest` tests mirroring `services/` and `utils/` | Tests for cogs (use integration tests for those) |
| `scripts/` | Shell scripts for deployment and maintenance | Python application code |

---

## 6. Phase 1 Features

These are the concrete commands the bot must implement in Phase 1. They serve as the development anchor — all architectural decisions are validated against these.

### `/ping`
Responds with `Pong!` and current latency. Used to verify the bot is alive.

### `/status`
Returns a system health summary for the Raspberry Pi: CPU usage, RAM usage, disk usage, and system uptime. Uses Python's `psutil` library.

### `/help`
Auto-generated command listing all available commands with a one-line description. Built using discord.py's built-in help system.

> **Note for AI agents:** all command logic lives in `cogs/`. The actual interaction with the NAS (HTTP calls, RPC) lives in `services/nas/`. Cogs only call service methods and format the response for Discord.

---

## 7. AI-Assisted Development — Prompt Roles

These are **not** autonomous parallel agents. They are **prompt modes** — structured instructions you activate in a single session (Aider CLI or IDE chat) at specific points in the workflow. The developer activates the relevant role for each type of task.

### Role Definitions

| Role | When to activate | What to ask |
|---|---|---|
| **Architecture** | Starting a new module or refactoring | "Acting as a software architect: design the structure for `services/nas/`, define the public interface, identify responsibilities" |
| **Implementation** | Writing code | Default mode — no special framing needed |
| **Code Review** | After implementing a feature | "Review this code for: PEP 8 compliance, error handling completeness, logging coverage, and adherence to the project structure defined in the README" |
| **Testing** | After implementation is reviewed | "Write `pytest` + `pytest-asyncio` tests for this service. Focus on: happy path, error cases, and edge cases. Do not test Discord cog methods directly." |
| **Documentation** | Before committing | "Write a docstring for this module/class/function following Google style" |
| **Deploy** | Preparing a release | "Generate a `systemd` unit file and a `deploy.sh` script for this project. Target: Raspberry Pi 4, Debian Bookworm, aarch64, Poetry environment" |


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
poetry run pytest --cov=pip_bot --cov-report=term-missing

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

## 11. Action Dispatcher — External Agent Protocol

This is the core integration point for Phase 2+. External agents communicate with pip-bot by sending structured messages to a **dedicated private Discord channel**. The bot listens on that channel, validates the message, and executes the requested action.

### Why a dedicated channel

- Separates automated commands from manual conversation
- Easy to audit: all agent requests are logged in one place
- Simple permission model: only you (and bots you authorise) can write to it

### Action registry (`services/actions/registry.py`)

Maps action names to service handler functions. Adding a new capability means registering a new action — no changes to the core bot or cogs.

```
"system.status"     → services.system.get_status()
```

### Security model (Phase 1 — simple)

- The actions channel is private: only you and explicitly authorised bots have write access
- The bot validates that the message author is on an allowlist defined in `.env`
- No cryptographic signing in Phase 1 — not needed for a single-owner private server

---

## 12. Roadmap

### Phase 1 — Foundation (current)

- [ ] Development environment: Python 3.11+, Poetry, IntelliJ + Aider
- [ ] GitHub repository: README, `.gitignore`, `.env.example`, initial structure
- [ ] Core bot: client, cog loader, global error handler, logging
- [ ] Cog: `system.py` — `/ping`, `/status`, `/help`
- [ ] Service + Cog: `nas/` — `/nas status`, `/nas list`, `/nas download`
- [ ] Service: `email/` — send plain text or HTML reports
- [ ] Tests for `services/nas/`, `services/email/`, and `utils/`
- [ ] Deployment on Raspberry Pi with `systemd`
- [ ] `deploy.sh` script for one-command updates

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | ✅ | Bot token from Discord Developer Portal |
| `DISCORD_GUILD_ID` | ✅ | Your server ID (for fast slash command registration in dev) |
| `LOG_LEVEL` | Optional | `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |

> Copy `.env.example` to `.env` and fill in your values. **Never commit `.env` to Git.**

---

## Contributing / AI Agent Instructions

This project is developed primarily by AI agents under human supervision. When generating or modifying code:

1. **Read this README first** — structure and conventions are non-negotiable
2. **One responsibility per file** — if a file needs to import from both `discord` and a third-party HTTP library, it probably belongs in a service, not a cog
3. **All secrets via `.env`** — no hardcoded values anywhere
4. **No bare `except`** — always catch specific exceptions and log them
5. **Logging over print** — use `utils/logger.py` to obtain a logger; never use `print()` in production code
6. **Commit with Conventional Commits** format — see Section 8
7. **ARM64 compatibility check** — before adding any dependency, confirm it has `linux_aarch64` wheels on PyPI
