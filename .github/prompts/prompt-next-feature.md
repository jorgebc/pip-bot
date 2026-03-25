Read README.md, ROADMAP.md, CHANGELOG.md, and .github/copilot-instructions.md before doing anything.

Identify the next pending milestone in ROADMAP.md — the first unchecked item in the current active phase.
If the current phase is complete, state it clearly and ask for confirmation before moving to the next phase.

Once the next milestone is identified, implement it following this exact sequence:

1. State clearly which milestone you are implementing and why it is the next one.
2. Implement the feature following the architecture and conventions in README.md and copilot-instructions.md:
   - Logic in services/, never in cogs/
   - Cogs only format responses and call services
   - No bare except — catch specific exceptions and log them
   - Use utils/logger.py for all logging, never print()
   - All secrets via .env — no hardcoded values
3. Write unit tests for every new or modified file in services/ and utils/:
   - Use pytest + pytest-asyncio
   - Mock all external I/O
   - Tests must mirror the source structure under tests/
4. Run linter and tests before finishing:
   - poetry run ruff check .
   - poetry run pytest
5. Update CHANGELOG.md: add a bullet under [Unreleased] describing what was added or changed.
6. Update ROADMAP.md: check off the completed milestone.
7. Bump the version in pyproject.toml:
   - New functionality → poetry version minor
   - Bug fix or adjustment → poetry version patch
   - Never bump MAJOR without explicit instruction
8. Propose a single Conventional Commits message for the final commit:
   - Format: type(scope): short description
   - Include CHANGELOG and ROADMAP updates in the same commit

Do not open a PR. Do not merge. Stop after proposing the commit message and wait for confirmation.