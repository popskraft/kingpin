# AI Agent — Testing & Workflow (Kingpin)

This is the single authoritative guide for AI agents working in this repo. It consolidates the content previously spread across multiple files.

## Required Actions

- After any change in `packages/engine/` — run full tests:
  ```bash
  cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python run_tests.py
  ```
- Before refactors — quick check:
  ```bash
  cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py quick
  ```
- After adding new code — full check:
  ```bash
  cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py full
  ```

## Interpreting Results

- ✅ 60+ passed — continue
- ❌ Any failed — stop and fix
- ⚠️ Coverage < 9% — investigate (target 15%+)

## Handy Commands

Quick check:
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py quick && echo "✅ Tests OK"
```

Full report:
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python run_tests.py
```

Module-specific:
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py module models
```

Critical trigger files:
- `packages/engine/models.py`
- `packages/engine/engine.py`
- `packages/engine/actions.py`

## Python API (optional)

```python
import sys
sys.path.append('/Users/popskraft/projects/kingpin')
from test_automation import quick_test_check, full_test_run, validate_test_environment

if quick_test_check():
    print("✅ Тесты прошли")
else:
    print("❌ Тесты провалились")

result = full_test_run()
print(f"Coverage: {result['stats']['coverage']['percentage']}%")
```

## Quality Metrics

- Tests: ≥ 60
- Coverage: ≥ 9% (goal 15%+)
- Quick check time: < 2s

Alerts:
- Tests < 60, any failures, coverage < 9%, import errors

## Workflow

1) Start: `validate` then `quick`
2) During: after every `packages/engine/` change → `run_tests.py`
3) Before refactor: `quick`
4) Finish: `run_tests.py` and confirm all pass

## Debugging

Imports:
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python -c "import packages.engine.models; print('OK')"
```

One test:
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && pytest tests/test_engine_models.py::TestCard::test_card_creation_basic -v
```

Coverage HTML:
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && pytest tests/test_engine_models.py tests/test_engine_core.py --cov=packages --cov-report=html
# Open htmlcov/index.html
```

