import sys
from pathlib import Path
import pytest

# Ensure project root is on sys.path so 'packages' is importable when running pytest
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def clean_globals():
    """Очистка глобальных переменных перед тестом"""
    try:
        from packages.server.main import rooms, sid_index
        rooms.clear()
        sid_index.clear()
        yield
        rooms.clear()
        sid_index.clear()
    except ImportError:
        # Если модули сервера недоступны, просто пропускаем
        yield
