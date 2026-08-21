# AGENTS.md

WinSnap is a Windows-only Python 3.10+ CLI (pure stdlib, no runtime deps) that snapshots Windows system state to JSON and diffs snapshots. Tests use `unittest`, not pytest.

## Commands
- Tests: `python -m unittest discover -s tests -p "test*.py"`. No linter/formatter/typechecker is configured.
- CI (`.github/workflows/ci.yml`) also runs: `python -m compileall winsnap`, CLI smoke (`python -m winsnap --version`, `python -m winsnap help`), `python -m build`, and a fresh-venv wheel-install smoke.
- Run without installing: `python -m winsnap ...` or `.\winsnap.cmd ...`.
- CWD matters: snapshots are written to `snapshots/` relative to the current directory (`winsnap/snapshot_store.py`). Run commands from the project root.

## Frozen surface (do not change casually)
- The 10-collector set and snapshot schema v1 are frozen (`winsnap/artifacts.py` `SUPPORTED_COLLECTORS`/`ARTIFACTS`, `docs/SCHEMA.md`). Don't add collectors or bump the schema without a release-level decision.
- `winsnap/artifacts.py` is the wiring hub: it maps each collector to its diff, view/print functions, search fields, and summary fields. Most features touch this registry plus `winsnap/differ.py` and `winsnap/views/`.
- Diffs never delete evidence: `winsnap/filtering/engine.py` only deprioritizes/re-pairs items and stores them under `_filtered` keys; `--all` restores everything. Preserve filtered items; never drop them.

## Native / toolchain quirks
- `winsnap/files/signature.py` calls WinVerifyTrust via ctypes and `winsnap/files/hashing.py` hashes executables; both are Windows-only. Some tests (`test_native_signature.py`, `test_native_network.py`) exercise native APIs/temp files — don't port them off Windows.
- PowerShell-based collectors (`winsnap/collectors/powershell.py`) honor the `WINSNAP_TIMEOUT_FACTOR` env var set by `create --timeout-factor`.
- `create --fast` = `--no-hash --no-signature`; `--cache` reuses `snapshots/.hashcache.json` keyed by size+mtime. README warns size+mtime are spoofable, so keep caching opt-in.
- `winsnap/cli.py` uses a custom argparse subclass that raises `ValueError` (not `SystemExit`) on bad args; errors are caught in `main()`.

## Release
- Bump the version in both `pyproject.toml` and `winsnap/version.py` (also README and `docs/SCHEMA.md`). `publish.yml` fails unless the git tag equals `v<pyproject version>`. Release by creating a GitHub release; PyPI uses trusted publishing.
