Contributing to WinSnap
=======================

Thanks for your interest in contributing!

Getting Started
---------------
- Windows 10/11 recommended
- Python 3.10+ (CI also tests 3.12)

Setup:
```powershell
python -m pip install -e .
python -m pip install build
python -m unittest discover -s tests -p "test*.py"
```

Code Style
----------
- Prefer small, focused changes
- Keep artifact schemas stable (frozen for v1.0)
- Validate snapshots before use; never delete evidence

Tests
-----
- Add or update tests under `tests/`
- Use `unittest` (CI runs `python -m unittest`)

Pull Requests
-------------
- Describe why the change is needed
- Include tests for important logic
- Avoid adding new collectors before v1.0 (collector set is frozen)

Thank you!
