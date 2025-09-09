"""
Дополнительные тесты для packages/engine/config.py:
- Ошибочные кейсы get_path/get_constant/get_csv_columns
- Загрузка конфига и перезагрузка GameConfig
"""

import io
import os
from pathlib import Path
import tempfile
import pytest

from packages.engine import config as cfg


def test_get_path_unknown_key_raises():
    with pytest.raises(ValueError):
        cfg.get_path("nonexistent")


def test_get_constant_unknown_key_raises():
    with pytest.raises(ValueError):
        cfg.get_constant("nope")


def test_get_csv_columns_unknown_field_raises():
    with pytest.raises(ValueError):
        cfg.get_csv_columns("wrong")


def test_game_config_reload_reads_new_values(tmp_path: Path):
    # создаём временный yaml, чтобы не трогать проектный файл
    yaml1 = tmp_path / "test.yaml"
    yaml1.write_text("hand_limit: 6\n", encoding="utf-8")
    g = cfg.GameConfig(config_path=yaml1)
    assert g.get("hand_limit") == 6

    # переписываем файл и проверяем reload
    yaml1.write_text("hand_limit: 8\n", encoding="utf-8")
    g.reload()
    assert g.get("hand_limit") == 8

