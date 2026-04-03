# CLAUDE.md — pip-bot

Context file for Claude Code sessions. Read this before writing any code.

---

## First-time setup

```bash
poetry install                  # installs main + dev deps
poetry run pre-commit install   # register commit hook (ruff + mypy)
poetry run pre-commit install --hook-type pre-push  # register push hook (pytest)
```

Run once per clone. After this, every `git commit` checks lint + types and every `git push` runs the full test suite — matching CI exactly.

## Commands

```bash
# Run bot locally
poetry run python -m bot

# Tests
poetry run pytest
poetry run pytest --cov=. --cov-report=term-missing
poetry run pytest tests/services/nas/test_client.py  # single file

# Lint / format
poetry run ruff check .
poetry run ruff format .

# Type check (mirrors CI)
poetry run mypy bot/ cogs/ services/ config/ utils/

# Run all pre-commit checks manually (without committing)
poetry run pre-commit run --all-files
```

## Architecture

```
bot/        Discord client subclass, on_ready, cog loader. Entry: python -m bot
cogs/       Thin Discord command wrappers. Call services, format response. No logic here.
services/   Business logic and external integrations (psutil, Pi-hole API, NAS, email).
config/     .env loading → typed Settings dataclass. Use get_settings() everywhere.
utils/      logger.py only. Use get_logger(__name__) — never print().
tests/      Mirror source layout. Unit-test services/ and utils/. Do not unit-test cogs.
scripts/    deploy.sh, setup_rpi.sh — operational, not part of the bot.
```

## Current phase

Phase 1 — RPi control commands. See ROADMAP.md for open milestones.

Next to implement (in order):
1. `/temp` — CPU temperature (`/sys/class/thermal/thermal_zone0/temp`)
2. `/reboot` — RPi reboot with confirmation
3. `/logs [lines]` — tail journalctl output
4. `/network` — local IP, public IP, interfaces
5. `services/pihole/client.py` + `cogs/pihole.py` — Pi-hole API commands

## Feature implementation workflow

Follow this order every time — no exceptions:

1. **Service first** — implement business logic in `services/` with no Discord imports
2. **Tests** — write unit tests in `tests/` mirroring the source path; mock all external I/O
3. **Cog** — thin wrapper in `cogs/` that calls the service and formats the Discord response
4. **Docstrings** — Google style on all public functions and classes
5. **Commit + update docs** — Conventional Commit + CHANGELOG + version + README/ROADMAP if needed

## Testing

- Framework: `pytest` + `pytest-asyncio`
- Mark every async test with `@pytest.mark.asyncio`
- Mock all external I/O at the `services/` boundary — no real network calls in tests
- Test file mirrors source: `services/pihole/client.py` → `tests/services/pihole/test_client.py`
- `services/` and `utils/` must have full unit tests
- `config/` tested with `monkeypatch` for env vars
- `cogs/` are not unit-tested directly — test the services they call

## Non-negotiable rules

- **One responsibility per file.** If a file needs both `discord` and an HTTP client, the HTTP logic belongs in `services/`, not `cogs/`.
- **No bare `except`.** Always catch specific exceptions and log them.
- **Secrets via `.env` only.** Read through `config/settings.py`. Never hardcode values.
- **Async-first.** Blocking I/O (psutil, file reads, HTTP) must run in `asyncio.to_thread()` or `loop.run_in_executor()`.
- **ARM64 check.** Before adding a dependency, confirm `linux_aarch64` wheels exist on PyPI.
- **Tests for services.** Every new `services/` module needs unit tests with mocked I/O.

## Conventions

- Loggers: `logger = get_logger(__name__)` at module level.
- Commits: Conventional Commits — `type(scope): description` (e.g. `feat(pihole): add /pihole status`).
- Docstrings: Google style on all public functions and classes.
- Version: patch for fixes, minor for completed phases. Bump in same commit that closes a PR.
- CHANGELOG: update `[Unreleased]` on every PR. Convert to versioned entry on release.

## On every PR — checklist

Before committing, always update these if the change warrants it:

| File | When to update |
|---|---|
| `CHANGELOG.md` | Every PR — add bullet under `[Unreleased]` |
| `pyproject.toml` | Bug fix → patch, new feature/phase → minor |
| `README.md` | New command added or status changed (✅/⏳) |
| `ROADMAP.md` | Milestone completed → check the box; new milestone planned → add it |

## Deployment

- Target: Raspberry Pi 4, Debian Bookworm 64-bit, systemd service `pip-bot`.
- Deploy: `git push` on PC → `scripts/deploy.sh` on RPi (git pull + poetry install + systemctl restart).
- Logs: `journalctl -u pip-bot -f`

## Environment variables (Phase 1)

| Variable | Required | Notes |
|---|---|---|
| `DISCORD_TOKEN` | yes | Bot token |
| `DISCORD_GUILD_ID` | yes | Server ID for fast guild sync |
| `LOG_LEVEL` | no | Default `INFO` |
| `STARTUP_CHANNEL_ID` | no | Channel for online notification |
