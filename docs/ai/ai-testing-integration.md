# AI Testing — Integration

## 📋 Правила для user_rules

Добавьте следующие правила в ваш user_rules для автоматического тестирования проекта Kingpin:

```markdown
## Автоматическое тестирование проекта Kingpin

### Обязательные действия при работе с кодом:

1. **После изменений в packages/engine/** - ВСЕГДА запускать тесты:
   ```bash
   cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python run_tests.py
   ```

2. **Перед рефакторингом** - проверить текущее состояние тестов:
   ```bash
   cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py quick
   ```

3. **После добавления нового кода** - запустить полную проверку:
   ```bash
   cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py full
   ```

### Интерпретация результатов:

- ✅ **60+ passed** - можно продолжать разработку
- ❌ **Любые failed** - ОСТАНОВИТЬ работу, исправить тесты
- ⚠️ **Coverage < 9%** - проверить что не сломалось

### Быстрые команды для копирования:

**Быстрая проверка:**
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py quick && echo "✅ Tests OK"
```

**Полная проверка с отчётом:**
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python run_tests.py
```

**Проверка конкретного модуля:**
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py module models
```

### Критические файлы-триггеры:
- `packages/engine/models.py` - обязательно тестировать
- `packages/engine/engine.py` - обязательно тестировать  
- `packages/engine/actions.py` - обязательно тестировать

### Автоматическое поведение:
1. При успехе - кратко сообщить "✅ Tests passed"
2. При провале - подробно разобрать ошибки и исправить
3. При снижении покрытия - выяснить причину
```

## 🔧 Готовые команды для агента

### **Команды для tool calls:**

#### 1. Быстрая проверка тестов
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py quick
```

#### 2. Полный запуск с отчётом  
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python run_tests.py
```

#### 3. Проверка окружения
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py validate
```

#### 4. Тестирование конкретного модуля
```bash
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py module models
```

### **Python API для программного использования:**

```python
# В коде агента можно использовать:
import sys
sys.path.append('/Users/popskraft/projects/kingpin')

from test_automation import quick_test_check, full_test_run, validate_test_environment

# Быстрая проверка
if quick_test_check():
    print("✅ Тесты прошли")
else:
    print("❌ Тесты провалились")

# Полная информация
result = full_test_run()
print(f"Покрытие: {result['stats']['coverage']['percentage']}%")
```

## 📊 Мониторинг качества кода

### **Ключевые метрики:**
- **Количество тестов:** ≥60 (текущий базовый уровень)
- **Покрытие кода:** ≥9% (минимум), цель 15%+
- **Время выполнения:** <2 секунд для быстрой проверки

### **Сигналы тревоги:**
- 🚨 Количество тестов упало ниже 60
- 🚨 Покрытие упало ниже 9%
- 🚨 Любые failed тесты
- 🚨 Ошибки импорта модулей

## 🎯 Workflow интеграция

### **Начало сессии разработки:**
1. `python test_automation.py validate` - проверка готовности
2. `python test_automation.py quick` - проверка текущего состояния

### **Во время разработки:**
1. После каждого изменения в `packages/engine/` → `python run_tests.py`
2. Перед рефакторингом → `python test_automation.py quick`
3. После добавления функции → `python test_automation.py module <module>`

### **Завершение сессии:**
1. `python run_tests.py` - финальная проверка
2. Убедиться что все 60+ тестов проходят
3. Проверить покрытие ≥9%

## 🚀 Расширенные возможности

### **Для отладки проблем:**
```bash
# Проверка импортов
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python -c "import packages.engine.models; print('OK')"

# Запуск одного теста
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && pytest tests/test_engine_models.py::TestCard::test_card_creation_basic -v

# Детальный вывод ошибок
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && pytest tests/test_engine_models.py -v --tb=long
```

### **Для анализа покрытия:**
```bash
# HTML отчёт
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && pytest tests/test_engine_models.py tests/test_engine_core.py --cov=packages --cov-report=html

# Открыть отчёт: htmlcov/index.html
```

## 📝 Шаблоны ответов агента

### **При успешных тестах:**
```
✅ Тесты пройдены (60 тестов, покрытие 9.13%)
Продолжаю работу...
```

### **При провале тестов:**
```
❌ Обнаружены проблемы в тестах:
[детали ошибок]

Исправляю проблемы перед продолжением...
```

### **При изменении кода:**
```
🔧 Внесены изменения в packages/engine/models.py
🧪 Запускаю тесты для проверки...
[результат тестов]
```

---

**💡 Помните:** Эти правила обеспечивают автоматическое поддержание качества кода и предотвращают регрессии!
