Read README.md and .github/copilot-instructions.md before doing anything.

You are acting as a senior software engineer reviewing the current branch before it is merged.
Do not modify any code. Only analyse and report.

Review the changes in this branch against the following criteria:

Architecture:
- Are responsibilities correctly separated? (logic in services/, thin cogs, pure utils/)
- Does any file violate the single responsibility principle?
- Does any cog contain business logic or external I/O that should be in services/?
- Is services/actions/registry.py the only place where new actions are registered?

Code quality:
- Are there any bare except clauses?
- Is print() used anywhere instead of the logger?
- Are there hardcoded secrets or values that should be in .env?
- Are all public functions and classes documented with docstrings?

Testing:
- Does every new or modified file in services/ and utils/ have a corresponding test?
- Do tests mock all external I/O?
- Are async tests marked with @pytest.mark.asyncio?
- Run poetry run pytest and report the result

Conventions:
- Does the code follow ruff rules? Run poetry run ruff check . and report
- Are imports clean and ordered?
- Does the proposed commit message follow Conventional Commits format?

Project tracking:
- Has CHANGELOG.md been updated with an entry under [Unreleased]?
- Have completed milestones been checked off in ROADMAP.md?
- Has the version in pyproject.toml been bumped correctly?
- Is the version bump consistent with the type of change (patch/minor)?

Deliver your review as a structured report with these sections:
✅ Looks good, ⚠️ Minor issues, 🔴 Must fix before merging.
For each issue found, include the file name, the problem, and a suggested fix.