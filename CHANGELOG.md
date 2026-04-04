# Changelog

All notable changes to pip-bot are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Fixed
- `scripts/deploy.sh` — `grep -v` returns exit code 1 on a clean working tree; with `set -e` this caused the script to silently abort after backing up `.env`. Added `|| true` so a zero-match result is not treated as an error.

## [1.6.1] — 2026-04-04

### Fixed
- `cogs/system.py` — `/logs` command message truncation now accounts for the `*(output truncated — showing tail)*\n` prefix (37 chars) in the 2000-character Discord limit, preventing a `400 Bad Request` error when long output was returned

## [1.6.0] — 2026-04-03

### Fixed
- `services/system.py` — replaced all `asyncio.get_event_loop()` calls with `asyncio.get_running_loop()` to eliminate deprecation warning on Python 3.12+
- `services/system.py` — changed `psutil.cpu_percent(interval=None)` to `interval=0.5` for an accurate one-sample CPU reading (safe inside `run_in_executor`)
- `bot/client.py` — added `_ready` flag to guard `on_ready()` against duplicate command syncs and startup messages on Discord gateway reconnects
- `utils/filters.py` — tightened `TokenSanitizationFilter` regex to the exact three-segment Discord token format, reducing false positives on UUIDs and base64 strings in debug logs; fixed dangling `\1` back-reference in substitution
- `utils/logger.py` — call `os.chmod(log_dir, 0o700)` after creating `logs/` so only the bot owner can read log files
- `scripts/deploy.sh` — add `git status --porcelain` check before `git reset --hard` to warn about modified/untracked files that would be silently discarded (`.env` excluded, already backed up)
- `scripts/setup_rpi.sh` — add `check_reboot_sudoers()` that inspects `sudo -l -n` for a NOPASSWD reboot rule and prints the exact `visudo` line to add if it is missing
- `tests/services/test_system.py` — updated `cpu_percent` assertion from `interval=None` to `interval=0.5`

### Added
- `pyproject.toml` — added `pytest-cov`, `mypy`, `bandit[toml]`, and `pip-audit` to `[dependency-groups] dev` so security and coverage tools run locally, not just in CI
- `pyproject.toml` — `[tool.pytest.ini_options]` with `--cov`, `--cov-report=term-missing`, and `--cov-fail-under=85` to enforce coverage threshold on every test run
- `pyproject.toml` — `[tool.mypy]`, `[tool.bandit]`, and `[tool.ruff]` sections to pin tool behaviour across version upgrades
- `.github/workflows/pr-validation.yml` — `mypy` type-check step; `bandit` now reads config via `-c pyproject.toml`; added `pytest-cov` and `mypy` to CI install
- `utils/concurrency.py` — `run_blocking(fn, *args)` helper wrapping `loop.run_in_executor(None, fn, *args)` to eliminate repeated boilerplate in service modules
- `cogs/_views.py` — `RebootConfirmView` extracted from `cogs/system.py`; dedicated module for reusable Discord UI components

### Refactored
- `services/system.py` — all four async wrappers now use `run_blocking()` from `utils/concurrency`; removed unused `asyncio` import
- `services/nas/client.py` — `NASClient` now inherits `BaseService` with `NotImplementedError` stubs for all abstract methods
- `services/email/client.py` — `EmailClient` now inherits `BaseService` with `NotImplementedError` stubs for all abstract methods
- `services/actions/handler.py`, `services/actions/registry.py` — stub functions with Google-style docstrings and `NotImplementedError`

---

## [1.5.0] — 2026-04-03

### Added
- `services/system.py` — `get_journal_logs(lines)` synchronous function that runs `journalctl -u pip-bot -n <lines> --no-pager`; raises `subprocess.CalledProcessError` on non-zero exit, `FileNotFoundError` if journalctl is absent, `OSError` on execution failure; lines is clamped to [1, 50]
- `services/system.py` — `get_journal_logs_async(lines)` async wrapper that runs the blocking call in a thread pool via `loop.run_in_executor()`
- `cogs/system.py` — `/logs [lines]` slash command: displays the last N lines (default 20, max 50) from the bot's systemd journal in a code block; gracefully handles non-systemd systems and truncates output that exceeds the Discord 2000-character limit
- `tests/services/test_system.py` — 8 new unit tests for `get_journal_logs()` and `get_journal_logs_async()` covering normal output, argument passing, line clamping (min/max), `CalledProcessError`, `FileNotFoundError`, `OSError`, and async delegation

---

## [1.4.1] — 2026-04-03

### Added
- `.github/workflows/pr-validation.yml` — PR validation CI: ruff lint, pytest, pip-audit, bandit in a single job
- `.github/dependabot.yml` — weekly Dependabot configuration for the `pip` ecosystem targeting `main`

---

## [1.4.0] — 2026-04-03

### Added
- `services/system.py` — `reboot_system()` synchronous function that executes `sudo reboot` via subprocess; raises `subprocess.CalledProcessError` on non-zero exit, `OSError` if the binary is missing
- `services/system.py` — `reboot_system_async()` async wrapper that runs the blocking call in a thread pool via `loop.run_in_executor()`
- `cogs/system.py` — `/reboot` slash command with a 30-second confirmation step using `discord.ui.View` with Confirm (red) and Cancel (grey) buttons; reboot only proceeds on explicit confirmation; handles timeout gracefully
- `tests/services/test_system.py` — 4 new unit tests for `reboot_system()` and `reboot_system_async()` covering normal execution, `CalledProcessError`, `OSError`, and async delegation

---

## [1.3.1] — 2026-04-03

### Fixed
- `scripts/deploy.sh` — replaced removed `--no-dev` flag with `--only main` for Poetry ≥ 2.x compatibility
- `scripts/deploy.sh` — added `rm -f poetry.lock` before install to force regeneration from `pyproject.toml`, preventing stale lock file conflicts
- `scripts/deploy.sh` — added explicit `poetry lock` step before `poetry install --only main` to ensure the lock file is always valid on the target environment

---

## [1.3.0] — 2026-04-02

### Added
- `services/system.py` — `get_cpu_temperature()` reads millidegree Celsius value from `/sys/class/thermal/thermal_zone0/temp` and returns degrees Celsius; raises `FileNotFoundError` on non-Linux systems, `OSError` on read failure, `ValueError` on bad content
- `services/system.py` — `get_cpu_temperature_async()` async wrapper that runs the blocking read in a thread pool via `loop.run_in_executor()`
- `cogs/system.py` — `/temp` slash command: displays current CPU temperature in a color-coded embed (green below 70°C, red at 70°C or above); gracefully handles `FileNotFoundError` when not running on a Linux/RPi system
- `tests/services/test_system.py` — 6 new unit tests for `get_cpu_temperature()` covering normal conversion, whitespace stripping, `FileNotFoundError`, `OSError`, `ValueError`, and high-temperature path

---

## [1.2.2] — 2026-04-02

### Fixed
- `bot/client.py` — added `tree.copy_global_to(guild=guild)` before `tree.sync(guild=guild)` in `on_ready`; slash commands decorated with `@app_commands.command` inside a Cog register to the global tree, not the guild tree, so guild sync was returning 0 commands and the bot was not responding to any slash command
- `bot/client.py` — split sync error handling into `discord.Forbidden` (missing `applications.commands` OAuth scope) and `discord.HTTPException` for clearer diagnosis

### Added
- `bot/client.py` — startup channel notification: when `STARTUP_CHANNEL_ID` is set, the bot posts an online message to that channel on every `on_ready`, including the number of synced commands
- `bot/client.py` — disconnect timestamp tracking: `on_disconnect` records the exact UTC time; `on_resumed` logs the downtime duration in seconds
- `bot/client.py` — per-command DEBUG log after sync listing each registered command name
- `config/settings.py` — optional `startup_channel_id` field read from `STARTUP_CHANNEL_ID` env var
- `.env.example` — documented `STARTUP_CHANNEL_ID` optional variable

---

## [1.2.1] — 2026-03-28

### Changed
- README.md: Updated Phase 1 features section with implementation status (3/5 commands complete)
- README.md: Updated Tech Stack section with actual dependencies and versions from pyproject.toml
- README.md: Refactored Section 7 (AI-Assisted Development) with clearer guidance for code assistants
- README.md: Expanded Section 11 (Services AI Layer) with detailed action registry and security model
- README.md: Added "Key implementation details" subsection with service layer documentation
- README.md: Updated environment variables reference table with Phase 2–3 variables and validation rules
- README.md: Reorganized contributing guidelines with practical testing checklist
- ROADMAP.md: Added current status header noting Phase 1 is ~90% complete
- .env.example: Enhanced documentation for Phase 2–3 variables with validation notes and SMTP examples

### Added
- Environment variable documentation for Phase 3 (ACTIONS_CHANNEL_ID, ALLOWED_AGENT_IDS, SMTP_*)
- Testing checklist in Contributing section (pytest, coverage, ruff checks)
- Example workflow for Phase 2 NAS integration in Section 7

---

## [1.2.0] — 2026-03-28

### Added
- `utils/filters.py` — TokenSanitizationFilter for preventing credential leakage in logs via regex sanitization of tokens and sensitive keys
- Discord reconnection handlers in bot/client.py: `on_error()`, `on_disconnect()`, `on_resumed()` for improved stability monitoring
- `services/system.py` — New `get_system_status_async()` function that runs blocking psutil calls in thread pool to prevent event loop blocking
- `services/base.py` — Abstract base class for all pip-bot services defining common interface for Phase 2+ implementations
- `tests/test_imports.py` — Import verification tests to detect circular dependencies and ensure module structure integrity

### Changed
- `utils/logger.py` — Integrated TokenSanitizationFilter to all handlers (console and file) to sanitize tokens and sensitive data in exception tracebacks
- `bot/__main__.py` — Added specific exception handling for discord.LoginFailure and discord.HTTPException to provide clearer error messages and prevent token leakage in generic exceptions
- `pip-bot.service` — Added resource limits (MemoryLimit=800M, OOMPolicy=kill, TasksMax=50, CPUQuota=80%) to protect Raspberry Pi from memory exhaustion and runaway processes
- `services/system.py` — Changed `psutil.cpu_percent(interval=1)` to non-blocking `interval=None` for instant sampling
- `cogs/system.py` — Updated `/status` command to use new `get_system_status_async()` function that runs blocking psutil calls in thread pool via `loop.run_in_executor()`
- `cogs/system.py` — Added rate limiting via `@app_commands.checks.cooldown(1, 60)` to all commands (/ping, /status, /help) and asyncio.timeout() for Discord API calls

### Fixed
- `config/settings.py` — NAS configuration validation: enforces all-or-none rule (if NAS_HOST is set, all of NAS_HOST, NAS_PORT, NAS_USER, NAS_PASSWORD must be set)
- `scripts/deploy.sh` — Added .env backup/restore logic before and after git reset to prevent accidental loss of configuration during deployment
- `scripts/deploy.sh` — Improved error reporting by capturing stderr from poetry install failures instead of silently discarding output
- `pip-bot.service` — Updated ExecStart to use PATH-based poetry resolution instead of hardcoded path, with ExecStartPre check for poetry availability
- `cogs/system.py` — Improved exception handling in all commands with timeout protection (5s for /ping, 15s for /status, 10s for /help) and graceful error messaging
- `.gitignore` — Added .env* pattern to ignore environment file backups and variants

---

## [1.0.1] — 2026-03-26

### Fixed
- `.env.example` — Improved documentation with clear sections for Phase 1 variables, Discord setup instructions, and future phases
- `scripts/setup_rpi.sh` — Enhanced error handling for Poetry installation and PATH issues:
  * Better Poetry binary detection (check standard location before PATH)
  * Improved error messages with manual recovery steps
  * Better handling of Poetry not being in PATH after installation
  * More detailed summary output with ASCII boxes and clearer next steps
  * Better logging output for dependency installation
- `scripts/deploy.sh` — Improved Poetry PATH handling to avoid failures when Poetry is not in PATH

---

## [1.0.0] — 2026-03-26

### Added
- `scripts/setup_rpi.sh` — first-time Raspberry Pi setup automation with:
  * Repository cloning from GitHub
  * Poetry installation in user directory
  * Python dependency installation (--no-dev)
  * Environment configuration from .env.example
  * Systemd service installation and enablement
  * Prerequisite verification (git, Python 3, disk space)
  * Color-coded logging and helpful progress messages
  * Interactive prompts for confirmation on existing installations
  * Comprehensive next-steps guidance with manual configuration instructions
  * Support for custom repository URLs via REPO_URL environment variable

### Changed
- ROADMAP.md: Marked Phase 1 "setup_rpi.sh" milestone as completed (Phase 1 complete!)

---

## [0.6.0] — 2026-03-26

### Added
- `scripts/deploy.sh` — one-command deployment script for Raspberry Pi with:
  * Git pull from origin/main to update code
  * Poetry dependency installation (--no-dev)
  * Automatic systemd service restart
  * Prerequisite verification (Poetry path, systemd availability)
  * Color-coded logging for easy debugging
  * Comprehensive error handling with helpful error messages
  * Pre-deployment and post-deployment health checks
  * Usage instructions and deployment summary

### Changed
- ROADMAP.md: Marked Phase 1 "deploy.sh" milestone as completed

---

## [0.5.0] — 2026-03-26

### Added
- `pip-bot.service` — systemd unit file for running bot as a service on Raspberry Pi with:
  * Automatic startup on system boot via `systemctl enable`
  * Automatic restart on failure (10-second backoff)
  * User isolation (runs as `pi` user, not root)
  * Proper working directory and environment setup
  * Journal logging integration for easy debugging via `journalctl`
  * Unbuffered Python output for real-time log capture

### Changed
- ROADMAP.md: Marked Phase 1 "systemd unit file" milestone as completed

---

## [0.4.0] — 2026-03-26

### Added
- `cogs/system.py` — `/help` command with:
  * Auto-discovery of all available bot commands from loaded cogs
  * Fallback to hardcoded System commands when no cogs found
  * Description truncation at 80 characters for proper embed formatting
  * Ephemeral responses (only visible to command invoker)
  * Comprehensive error handling with user-friendly messages
- Unit tests for `/help` command:
  * 5 comprehensive test methods covering success case, cog discovery, fallback behavior, error handling, and description truncation
  * All tests passing with proper mocking of bot and interaction objects

### Changed
- ROADMAP.md: Marked Phase 1 "/help auto-generated command list" milestone as completed

---

## [0.3.0] — 2026-03-26

### Added
- `services/system.py` — system health monitoring service with:
  * `get_system_status()` function collecting CPU, RAM, disk usage, and uptime
  * `SystemStatus` dataclass for structured metrics
  * Helper function `_format_timedelta()` for human-readable uptime strings
  * Proper error handling and logging
- `cogs/system.py` — system commands cog with:
  * `/ping` slash command showing bot latency
  * `/status` slash command displaying system health metrics in a rich embed
  * Comprehensive error handling with user-friendly messages
  * `setup()` function for cog loading
- Unit tests for services/system.py:
  * 10 comprehensive tests covering all functions and edge cases
  * Mocking of psutil calls to avoid platform-specific issues
  * Tests for timedelta formatting, metric collection, and error handling
- Unit tests for cogs/system.py:
  * 8 comprehensive tests for both commands and cog initialization
  * Tests for latency variations, error handling, and cog loading
- Updated `bot/client.py`:
  * Implemented `setup_hook()` to load the SystemCog automatically on bot startup
  * Added proper error handling for cog loading failures

### Changed
- ROADMAP.md: Marked Phase 1 "/ping and /status commands" milestone as completed

---

## [0.2.0] — 2026-03-25

### Added
- `bot/client.py` — PipBot Discord client subclass with:
  * Customized intents (message_content, guilds enabled)
  * on_ready event handler for logging startup status and syncing slash commands to guild
  * setup_hook for future cog loading
  * Proper error handling for command sync failures
- `bot/__init__.py` — Exports PipBot class
- `bot/__main__.py` — Entry point for running bot with `python -m bot`
  * Loads settings, creates bot instance, handles startup and errors
- Unit tests for bot/client.py:
  * 7 comprehensive tests covering initialization, intents, on_ready behavior, and setup_hook
  * All tests passing with proper mocking of Discord API calls
  * Test coverage includes edge cases (missing user handling)

### Changed
- ROADMAP.md: Marked Phase 1 "bot/client.py + bot/__init__.py" milestone as completed
- Version bumped to 0.2.0 (minor version for feature completion)

---

## [0.1.1] — 2026-03-25

### Added
- `utils/logger.py` — centralized logger factory with rotating file handlers
  * Console handler for development (timestamp, level, module, message)
  * RotatingFileHandler for production (5MB per file, 3 backups, ~15MB max)
  * Configurable via LOG_LEVEL env var (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  * Singleton pattern to prevent duplicate handlers
  
- `config/settings.py` — type-safe environment configuration
  * Settings dataclass with Phase 1 required fields (DISCORD_TOKEN, DISCORD_GUILD_ID)
  * Optional fields for Phase 2+ (NAS_HOST, NAS_PORT, NAS_USER, NAS_PASSWORD)
  * Validation with clear error messages for missing/invalid variables
  * Caching mechanism to load .env only once
  
- Comprehensive test suites
  * 14 unit tests for config/settings.py (validation, caching, defaults, errors)
  * 15 unit tests for utils/logger.py (handlers, levels, formatting, file rotation)
  * All tests passing, edge cases covered

### Changed
- `pyproject.toml`: Fixed TOML syntax and added tool.poetry.packages configuration
- `config/__init__.py`: Exported Settings, get_settings, reset_settings, ConfigError
- `utils/__init__.py`: Exported get_logger
- `ROADMAP.md`: Marked logger and settings milestones as completed (Phase 1)

---

## [0.1.0] — 2026-03-22

### Added
- `README.md` — full project architecture, conventions, stack, roadmap, and AI agent protocol
- `.gitignore` — Python, Poetry, IntelliJ, and OS rules
- `pyproject.toml` — Poetry project with `discord.py`, `python-dotenv`, `psutil`, `pytest`, `pytest-asyncio`, `ruff`
- `.env.example` — environment variable template
- `.github/copilot-instructions.md` — Copilot/AI session guidance
- Full project folder structure with empty modules and docstrings (`bot/`, `cogs/`, `services/`, `config/`, `utils/`, `tests/`, `scripts/`)