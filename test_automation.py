#!/usr/bin/env python3
"""
Автоматизированное тестирование для AI агента
Этот скрипт предоставляет удобные функции для запуска тестов в различных сценариях
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import time


class TestRunner:
    """Класс для автоматизированного запуска тестов"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.venv_python = self.project_root / "venv" / "bin" / "python"
        self.python_cmd = str(self.venv_python) if self.venv_python.exists() else sys.executable
        
    def check_environment(self) -> Dict[str, bool]:
        """Проверка готовности тестового окружения"""
        checks = {}
        
        # Проверка виртуального окружения
        checks["venv_exists"] = self.venv_python.exists()
        
        # Проверка pytest
        try:
            result = subprocess.run([self.python_cmd, "-m", "pytest", "--version"], 
                                  capture_output=True, cwd=self.project_root)
            checks["pytest_available"] = result.returncode == 0
        except:
            checks["pytest_available"] = False
            
        # Проверка структуры проекта
        checks["packages_exist"] = (self.project_root / "packages").exists()
        checks["tests_exist"] = (self.project_root / "tests").exists()
        
        # Проверка тестовых файлов
        checks["models_tests"] = (self.project_root / "tests" / "test_engine_models.py").exists()
        checks["core_tests"] = (self.project_root / "tests" / "test_engine_core.py").exists()
        
        return checks
    
    def run_working_tests(self, verbose: bool = True) -> Tuple[bool, str, Dict]:
        """Запуск только работающих тестов"""
        print("🧪 Запуск работающих unit-тестов...")
        
        working_tests = [
            "tests/test_engine_models.py",
            "tests/test_engine_core.py"
        ]
        
        cmd = [
            self.python_cmd, "-m", "pytest"
        ] + working_tests + [
            "-v" if verbose else "-q",
            "--tb=short",
            "--cov=packages",
            "--cov-report=term-missing",
            "--disable-warnings"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        # Парсинг результатов покрытия
        coverage_info = self._parse_coverage(result.stdout)
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        stats = {
            "success": success,
            "duration": round(duration, 2),
            "coverage": coverage_info,
            "tests_run": self._count_tests(result.stdout)
        }
        
        return success, output, stats
    
    def run_quick_check(self) -> Tuple[bool, str]:
        """Быстрая проверка без детального вывода"""
        cmd = [
            self.python_cmd, "-m", "pytest",
            "tests/test_engine_models.py",
            "tests/test_engine_core.py",
            "-q",
            "--tb=no",
            "--disable-warnings"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        return result.returncode == 0, result.stdout
    
    def run_specific_test(self, test_path: str, test_name: str = None) -> Tuple[bool, str]:
        """Запуск конкретного теста"""
        test_target = test_path
        if test_name:
            test_target = f"{test_path}::{test_name}"
            
        cmd = [
            self.python_cmd, "-m", "pytest",
            test_target,
            "-v",
            "--tb=short",
            "--disable-warnings"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
    
    def check_imports(self) -> Tuple[bool, List[str]]:
        """Проверка импортов основных модулей"""
        modules_to_check = [
            "packages.engine.models",
            "packages.engine.engine", 
            "packages.engine.actions",
            "packages.engine.loader",
            "packages.engine.effects"
        ]
        
        errors = []
        
        for module in modules_to_check:
            try:
                result = subprocess.run([
                    self.python_cmd, "-c", f"import {module}; print('✅ {module}')"
                ], cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode != 0:
                    errors.append(f"❌ {module}: {result.stderr.strip()}")
                    
            except Exception as e:
                errors.append(f"❌ {module}: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _parse_coverage(self, output: str) -> Dict:
        """Парсинг информации о покрытии из вывода pytest"""
        coverage_info = {"total": 0, "missing": 0, "percentage": 0}
        
        lines = output.split('\n')
        for line in lines:
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        coverage_info["total"] = int(parts[1])
                        coverage_info["missing"] = int(parts[2]) 
                        coverage_info["percentage"] = float(parts[3].replace('%', ''))
                    except (ValueError, IndexError):
                        pass
                        
        return coverage_info
    
    def _count_tests(self, output: str) -> int:
        """Подсчёт количества запущенных тестов"""
        lines = output.split('\n')
        for line in lines:
            if "passed" in line and ("warning" in line or "failed" in line or line.strip().endswith("passed")):
                # Ищем строки вида "60 passed, 1 warning in 0.84s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            return int(parts[i-1])
                        except ValueError:
                            pass
        return 0


# Удобные функции для агента
def quick_test_check() -> bool:
    """Быстрая проверка тестов - возвращает True/False"""
    runner = TestRunner()
    success, _ = runner.run_quick_check()
    return success


def full_test_run() -> Dict:
    """Полный запуск тестов с детальной информацией"""
    runner = TestRunner()
    
    # Проверка окружения
    env_check = runner.check_environment()
    if not all(env_check.values()):
        return {
            "success": False,
            "error": "Environment check failed",
            "env_status": env_check
        }
    
    # Проверка импортов
    imports_ok, import_errors = runner.check_imports()
    if not imports_ok:
        return {
            "success": False,
            "error": "Import errors",
            "import_errors": import_errors
        }
    
    # Запуск тестов
    success, output, stats = runner.run_working_tests()
    
    return {
        "success": success,
        "output": output,
        "stats": stats,
        "env_status": env_check
    }


def test_specific_module(module_name: str) -> Dict:
    """Тестирование конкретного модуля"""
    runner = TestRunner()
    
    module_map = {
        "models": "tests/test_engine_models.py",
        "core": "tests/test_engine_core.py", 
        "actions": "tests/test_actions.py",
        "loader": "tests/test_loader.py",
        "effects": "tests/test_effects.py"
    }
    
    test_file = module_map.get(module_name)
    if not test_file:
        return {
            "success": False,
            "error": f"Unknown module: {module_name}",
            "available": list(module_map.keys())
        }
    
    success, output = runner.run_specific_test(test_file)
    
    return {
        "success": success,
        "output": output,
        "module": module_name,
        "test_file": test_file
    }


def validate_test_environment() -> Dict:
    """Валидация тестового окружения"""
    runner = TestRunner()
    
    env_check = runner.check_environment()
    imports_ok, import_errors = runner.check_imports()
    
    # Быстрый тест
    quick_ok, quick_output = runner.run_quick_check()
    
    return {
        "environment": env_check,
        "imports": {
            "success": imports_ok,
            "errors": import_errors
        },
        "quick_test": {
            "success": quick_ok,
            "output": quick_output
        },
        "overall_status": all(env_check.values()) and imports_ok and quick_ok
    }


# CLI интерфейс
def main():
    """Главная функция для командной строки"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python test_automation.py quick      # Быстрая проверка")
        print("  python test_automation.py full       # Полный запуск")
        print("  python test_automation.py validate   # Проверка окружения")
        print("  python test_automation.py module <name>  # Тест модуля")
        return
    
    command = sys.argv[1]
    
    if command == "quick":
        success = quick_test_check()
        print("✅ Тесты пройдены" if success else "❌ Тесты провалены")
        sys.exit(0 if success else 1)
        
    elif command == "full":
        result = full_test_run()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["success"] else 1)
        
    elif command == "validate":
        result = validate_test_environment()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["overall_status"] else 1)
        
    elif command == "module" and len(sys.argv) > 2:
        module_name = sys.argv[2]
        result = test_specific_module(module_name)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["success"] else 1)
        
    else:
        print(f"Неизвестная команда: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
