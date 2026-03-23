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

External agent model
- pip-bot contains no AI. It is a bridge: external agents (running on cloud platforms) do
  the work, compose a report, and send it to pip-bot via a private Discord channel.
- pip-bot receives the message, validates the sender, and executes the action (email, download, etc.).
- Agents are independent. They are not part of this codebase.
- See README Section 11 for the full message protocol.

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

Project tracking — CHANGELOG and ROADMAP
- CHANGELOG.md: updated on every merged PR. Add a bullet under [Unreleased] describing what changed.
  Format: "- Added / Fixed / Changed: <description>"
  Example: "- Added: /ping command in cogs/system.py"
- ROADMAP.md: check off milestones as they are completed. Do not add new milestones without
  discussing with the project owner first.
- When starting a session: read CHANGELOG.md [Unreleased] → Next to know what to implement.
- When closing a PR: update CHANGELOG.md and check off completed milestones in ROADMAP.md.
- Version: bump pyproject.toml version on every completed phase (poetry version minor)
    or on every fix (poetry version patch). Never bump MAJOR without explicit instruction.
    Run the bump in the same commit that closes the phase PR.

Files to prioritize in Copilot prompts
- README.md (architecture & conventions)
- ROADMAP.md (current phase and next milestone)
- CHANGELOG.md (what is done and what is next)
- pyproject.toml (deps & dev deps)
- .env.example
- bot/, cogs/, services/, config/, utils/, tests/

Guidance for Copilot sessions
- When implementing features: provide code + tests for services/ (mock external I/O) + docstrings + a Conventional Commit message.
- For refactors: preserve "one responsibility per file" and keep cogs minimal.
- For PRs: include unit tests for changed services, update CHANGELOG.md [Unreleased], check off completed milestones in ROADMAP.md.

If you want this expanded (CI steps, lint rules, or MCP server configuration), tell me which area to cover.