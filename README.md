# KINGPIN — тестовая среда карточной дуэльной игры

## Структура репозитория (сжатая)

- `packages/engine` — Python-движок (модели, правила, загрузчик CSV/YAML)
- `packages/server` — FastAPI + Socket.IO сервер (ASGI)
- `packages/simulator` — симулятор матчей и анализ баланса
- `webapp-2p` — фронтенд на React+Vite
- `config/` — конфигурации и `cards.csv` (единственный источник карточных данных)
- `docs/` — документация (структурирована):
  - `docs/rules.md` — правила игры
  - `docs/ai/` — инструкции для AI-агентов (тестирование)
  - `docs/analysis/` — аналитика и отчёты по качеству
  - `docs/reports/` — итоговые отчёты симуляций/баланса
  - `docs/architecture/` — архитектурные заметки
- `scripts/` — служебные утилиты и анализаторы
- `tests/` — unit-тесты

Полная схема папок и ссылки на ключевые документы приведены ниже.

## Структура проекта

- **packages/engine** — Python-движок (data-driven), загрузка правил из YAML
- **packages/simulator** — CLI-симулятор для автопрогонов и тестов
- **packages/server** — FastAPI + Socket.IO сервер комнат для 2 игроков
- **webapp-2p** — веб-интерфейс на React+Vite+TypeScript
- **docs/** — локальная документация (Markdown)
- **config/** — конфигурация правил (YAML), легко править во время разработки
  - Все карточные данные загружаются из `config/cards.csv` (единый источник правды)

## Возможности веб-интерфейса

- 2 игровых поля (вы/оппонент), 6–9 видимых слотов на каждой стороне
- Зона руки с drag-and-drop на поле
- Перемещение карт: рука → слот, слот ↔ слот, слот → рука, сброс
- Переворот карты на вашем поле двойным кликом
- Добавление/удаление жетонов щитов на слотах, управление резервными деньгами
- Взятие карт, перемешивание колоды, настройка количества видимых слотов
- Фильтрация состояния в реальном времени: ваша рука видна только вам

## Требования

- Node 18+
- Python 3.10+

## Пошаговая инструкция по запуску

### Подготовка окружения

#### 1. Создание виртуального окружения Python
```bash
# Переходим в корневую папку проекта (работает из любого места в терминале)
cd /Users/popskraft/projects/kingpin

# Создаем виртуальное окружение (избегаем конфликтов с системными пакетами)
python3 -m venv venv
```

#### 2. Установка зависимостей Python
```bash
# Активируем виртуальное окружение и устанавливаем зависимости (из любого места)
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && pip install -r requirements.txt
```

#### 3. Установка зависимостей Node.js для фронтенда
```bash
# Переходим в папку веб-приложения и устанавливаем зависимости (из любого места)
cd /Users/popskraft/projects/kingpin/webapp-2p && npm install
```

### Запуск серверов

#### 4. Запуск backend сервера (FastAPI + Socket.IO)
```bash
# Запуск сервера (работает из любого места в терминале)
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && cd packages/server && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
**Результат**: Сервер запустится на http://127.0.0.1:8000

#### 5. Запуск frontend сервера (React + Vite)
```bash
# Запуск фронтенда (работает из любого места в терминале, в новом терминале)
cd /Users/popskraft/projects/kingpin/webapp-2p && npm run dev
```
**Результат**: Веб-приложение запустится на http://localhost:5173/

#### Открытие в браузере Windsurf

- В IDE Windsurf нажмите кнопку `Open Preview` для фронтенда.
- Приложение откроется по прокси-URL вида `http://127.0.0.1:PORT` (пример: `http://127.0.0.1:58069`). Этот порт назначается динамически IDE.
- Если вы запускаете проект вне Windsurf, открывайте напрямую `http://localhost:5173/`.

### Доступ к игре
Откройте фронтенд в двух вкладках для симуляции двух игроков:

- Если запускаете локально: http://localhost:5173
- Если в Windsurf: используйте прокси-URL превью (например, `http://127.0.0.1:58069`)

Каждая вкладка автоматически присоединится к одной комнате и получит место (P1/P2).

### Остановка серверов

#### Способ 1: Через терминал
- Нажмите `Ctrl+C` в каждом терминале где запущены серверы

#### Способ 2: Через команды
```bash
# Остановка backend сервера
pkill -f "uvicorn main:app"

# Остановка frontend сервера  
pkill -f "npm run dev"
```

### Запуск симулятора (демо)
```bash
# Запуск симулятора (работает из любого места в терминале)
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python -m packages.simulator.cli simulate --config config/default.yaml --seed 42 --turns 3
```

### 🚀 Быстрые команды для копирования

#### Полная установка (выполнить один раз):
```bash
# 1. Подготовка Python окружения
cd /Users/popskraft/projects/kingpin && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# 2. Подготовка Node.js окружения  
cd /Users/popskraft/projects/kingpin/webapp-2p && npm install
```

#### Ежедневный запуск (2 команды в разных терминалах):
```bash
# ТЕРМИНАЛ 1: Backend сервер
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && cd packages/server && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# ТЕРМИНАЛ 2: Frontend сервер
cd /Users/popskraft/projects/kingpin/webapp-2p && npm run dev
```

#### Тестирование проекта:
```bash
# Запуск unit-тестов
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python run_tests.py

# Быстрая проверка тестов
cd /Users/popskraft/projects/kingpin && source venv/bin/activate && python test_automation.py quick
```

## ⚠️ Устранение неполадок

### Проблемы с Python виртуальным окружением:
```bash
# Если команды не работают, убедитесь что venv создан:
cd /Users/popskraft/projects/kingpin && ls -la venv/

# Пересоздать venv если нужно:
cd /Users/popskraft/projects/kingpin && rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

### Проблемы с Node.js зависимостями:
```bash
# Очистка и переустановка npm пакетов:
cd /Users/popskraft/projects/kingpin/webapp-2p && rm -rf node_modules package-lock.json && npm install
```

### Проверка что серверы запущены:
```bash
# Проверка backend (должен отвечать):
curl http://127.0.0.1:8000

# Проверка портов:
lsof -i :8000  # backend
lsof -i :5173  # frontend
```

### Принудительная остановка серверов:
```bash
# Остановка всех процессов проекта:
pkill -f "uvicorn main:app"
pkill -f "npm run dev"
pkill -f "vite"
```

## Конфигурация (опционально)

Создайте файл `.env` в папке webapp-2p для переопределения настроек:

```
VITE_SERVER_URL=http://localhost:8000
VITE_ROOM=demo
```

См. `.env.example` для значений по умолчанию.

## Архитектура правил

- Конфигурация хранится в `config/*.yaml` (рука on/off, лимиты, экономика, события, каскад 2-2-2)
- Карты описываются данными: базовые параметры (HP/ATK/D/INF, фракция, тип), платные свойства и эффекты по id
- Эффекты реализуются как плагины (реестр функций), что позволяет добавлять/менять их без переписывания ядра
- Режимы: Базовый/Стандарт/Продвинутый настраиваются флагами в YAML

## Примечания

- Комната заполняется при 2 участниках; 3-я вкладка будет отклонена
- Изменяйте количество видимых слотов с помощью слайдера (6–9). Изменения применяются для каждого игрока
- Сброс принимает перетаскивания из вашей руки или ваших слотов
- Используйте источник данных YAML или CSV (переключатель в нижнем колонтитуле, влияет только при первом входе в комнату)

## Лицензия

WIP (определить позже).

## Полезные ссылки

- Правила игры: `docs/rules.md`
- Руководство для AI-агента: `docs/ai/agent_testing.md`
- Интеграция тестов для AI: `docs/ai/ai-testing-integration.md`
- Анализ качества кода: `docs/analysis/code-quality-analysis.md`
- План рефакторинга сервера: `docs/architecture/server-refactor-plan.md`
- Отчёт по симуляции турнира: `docs/reports/tournament-simulation-report.md`

## Материалы для AI-агентов

См. единый справочник по тестированию и рабочему процессу для ИИ:

`docs/ai/agent_testing.md`
