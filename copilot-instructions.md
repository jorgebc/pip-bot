# Copilot instructions — pip-bot

Purpose
- Short, repo-specific guidance for Copilot/AI sessions: build/test/lint commands, high-level architecture, and conventions to follow.

Build / Test / Lint
- Run the bot (development):
  - poetry run python -m bot
- All tests:
  - poetry run pytest
- Run a single test file or test function:
  - poetry run pytest tests/services/nas/test_client.py
  - poetry run pytest tests/services/nas/test_client.py::test_function_name
  - or use -k to match test names: poetry run pytest -k test_name
- Coverage:
  - poetry run pytest --cov=. --cov-report=term-missing
- Lint and format: poetry run ruff check . / poetry run ruff format .

High-level architecture (big picture)
- bot/: Discord client subclass, event hooks, and cog loader. Entry point: python -m bot
- cogs/: Thin Discord feature modules that format responses and call services. Keep logic minimal here.
- services/: Business logic and external integrations (NAS, email, action dispatcher). Primary testing surface.
- services/actions/: Action dispatcher — maps JSON commands received from external agents
  via a private Discord channel to service handlers. New capabilities = new entry in registry.py.
- config/: Environment loading and typed Settings (.env via python-dotenv).
- utils/: Pure helpers (logger factory, etc.).
- scripts/: Operational shell scripts for RPi deployment (systemd + deploy.sh).

Key conventions (repo-specific)
- One responsibility per file: move heavy logic (network/filesystem) into services/; cogs only format and call services.
- Action registry: register new external-agent actions in services/actions/registry.py; avoid touching core bot or cogs.
- Tests mirror source layout under tests/; unit-test services and utils, mocking all external I/O. Do not unit-test cogs directly.
- Use pytest + pytest-asyncio; mark async tests with @pytest.mark.asyncio.
- Environment/secrets: use .env (copy .env.example). Never commit secrets.
- Logging: use utils/logger.py for loggers; avoid print().
- Error handling: do not use bare except; catch specific exceptions and log them.
- Commits: follow Conventional Commits format: type(scope): short description (e.g., feat(nas): add /nas download).
- ARM64 (RPi) caution: confirm linux_aarch64 wheels for new dependencies before adding them.

Files to prioritize in Copilot prompts
- README.md (architecture & conventions)
- pyproject.toml (deps & dev deps)
- .env.example
- bot/, cogs/, services/, config/, utils/, tests/

AI assistant configs checked
- No CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules, CONVENTIONS.md, or other assistant-config files found in the repo.

Guidance for Copilot sessions
- When implementing features: provide code + tests for services/ (mock external I/O) + docstrings + a Conventional Commit message.
- For refactors: preserve "one responsibility per file" and keep cogs minimal.
- For PRs: include unit tests for changed services and an updated README snippet if public API changes.

If you want this expanded (CI steps, lint rules, or MCP server configuration), tell me which area to cover.
