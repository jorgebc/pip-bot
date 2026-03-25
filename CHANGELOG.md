# Changelog

All notable changes to pip-bot are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

### Changed

### Next
- Implement `/ping` slash command in cogs/system.py
- Implement `/status` slash command for system health checks

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