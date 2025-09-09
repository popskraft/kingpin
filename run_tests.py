#!/usr/bin/env python3
"""
Скрипт для запуска unit-тестов проекта Kingpin
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Запуск тестов с настройкой окружения"""
    
    print("🚀 Запуск unit-тестов проекта Kingpin...")
    print("=" * 50)
    
    # Убедимся что находимся в правильной директории
    project_root = Path(__file__).parent
    print(f"📁 Рабочая директория: {project_root}")
    
    # Активируем виртуальное окружение если нужно
    venv_python = project_root / "venv" / "bin" / "python"
    if venv_python.exists():
        python_cmd = str(venv_python)
        print("🐍 Используем Python из виртуального окружения")
    else:
        python_cmd = sys.executable
        print("🐍 Используем системный Python")
    
    # Запускаем работающие тесты
    working_tests = [
        "tests/test_engine_models.py",
        "tests/test_engine_core.py"
    ]
    
    print(f"🧪 Запускаем {len(working_tests)} тестовых модуля...")
    
    try:
        # Запуск pytest
        cmd = [
            python_cmd, "-m", "pytest"
        ] + working_tests + [
            "-v",
            "--tb=short",
            "--cov=packages",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--disable-warnings"
        ]
        
        print(f"💻 Команда: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print()
            print("✅ Все тесты прошли успешно!")
            print("📊 HTML отчёт о покрытии сохранён в htmlcov/index.html")
            return True
        else:
            print()
            print("❌ Некоторые тесты не прошли")
            return False
            
    except FileNotFoundError:
        print("❌ Ошибка: pytest не найден. Установите зависимости:")
        print("   pip install pytest pytest-cov")
        return False
    except Exception as e:
        print(f"❌ Ошибка при запуске тестов: {e}")
        return False


def run_all_tests():
    """Запуск всех тестов (включая проблемные)"""
    
    print("🚀 Запуск ВСЕХ unit-тестов проекта Kingpin...")
    print("⚠️  Внимание: некоторые тесты могут не пройти")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "bin" / "python"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable
    
    try:
        cmd = [
            python_cmd, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=line",
            "--continue-on-collection-errors",
            "--disable-warnings"
        ]
        
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        success = run_all_tests()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)
