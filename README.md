## Engineering Workflow (Quant Dev)

For the following workstreams:
- 量化开发
- 量化开发子窗口
- 量化开发子窗口2

Engineering rules are enforced:

1. Any code change / new code / new file MUST be recorded in **CHANGELOG.md** (preferred) or documented in README.
2. All changes MUST be synced via **git** with a **branch + commit** workflow.
3. Commit messages should follow conventional prefixes:
   - feat: new feature
   - fix: bug fix
   - refactor: refactor without behavior change
   - test: add/adjust tests
   - chore: scaffolding/docs/config

Recommended process:
1) `git checkout -b <type>/<topic>`
2) implement change
3) update `CHANGELOG.md` under `[Unreleased]`
4) run verification (at least runnable entrypoint / tests)
5) `git add . && git commit -m "<type>: <message>"`
