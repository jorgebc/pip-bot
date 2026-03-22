# Changelog

All notable changes to pip-bot are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Next
- Implement bot core: logger, settings, client, entry point
- Implement `/ping` slash command

---

## [0.1.0] — 2026-03-22

### Added
- `README.md` — full project architecture, conventions, stack, roadmap, and AI agent protocol
- `.gitignore` — Python, Poetry, IntelliJ, and OS rules
- `pyproject.toml` — Poetry project with `discord.py`, `python-dotenv`, `psutil`, `pytest`, `pytest-asyncio`, `ruff`
- `.env.example` — environment variable template
- `.github/copilot-instructions.md` — Copilot/AI session guidance
- Full project folder structure with empty modules and docstrings (`bot/`, `cogs/`, `services/`, `config/`, `utils/`, `tests/`, `scripts/`)