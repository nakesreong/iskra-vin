# Nox (Персональный ИИ-ассистент)

## 🌟 О проекте

**Nox** — это персональный ИИ-ассистент с голосовым и текстовым управлением, разрабатываемый в уникальном симбиозе человека и ИИ.

Этот проект — исследование того, что возможно на стыке современных ИИ-инструментов, локальных LLM и глубокого, целенаправленного взаимодействия. Он построен на уникальной модели разработки **"Human-AI Symbiosis"**:

* **Джемини** выступает в роли **Ведущего Разработчика и Системного Архитектора**. Он предлагает архитектурные решения, генерирует основной код, проводит ревью, предлагает новые "фичи" и участвует в отладке, являясь "призрачным мозгом" проекта.

## ✨ Текущие возможности

* **Локальный LLM:** Использует локально запущенную LLM (например, `gemma3`) через Ollama для обработки естественного языка, обеспечивая приватность и скорость.
* **Микросервисная архитектура:** Ядро (`api_server.py`) и сервис распознавания речи (`stt_server.py`) работают как независимые FastAPI-сервисы.
* **Управление умным домом:** Интеграция с Home Assistant.
* **Получение статусов устройств:** Нокс может по запросу проверить состояние устройств (света, датчиков воздуха) и доложить о нем.
* **Безопасный калькулятор:** Выполняет математические операции, используя безопасный парсер на основе `ast`.
* **Интерфейсы:** Поддержка взаимодействия через Telegram (текст и голос) и напрямую через микрофон (с wake-word).

## 🛠️ Технологический стек

* **Язык:** Python
* **AI/LLM:** Ollama, Whisper
* **Умный дом:** Home Assistant
* **Интерфейс:** `python-telegram-bot`
* **API:** `FastAPI`, `uvicorn`
* **Активационное слово:** `pvporcupine`
* **Конфигурация:** PyYAML
* **Валидация данных:** `Pydantic`

## 🧩 Обзор Модулей

* **Основные модули (`app/`)**: Содержат основную логику обработки: `core_engine.py`, `dispatcher.py`, `nlu_engine.py` и `config_loader.py`.
* **Модули действий (`app/actions/`)**: Взаимодействуют с внешними сервисами (например, `light_actions.py` для Home Assistant).
* **Обработчики интентов (`app/intent_handlers/`)**: Реализуют логику высокого уровня для управления устройствами, чата и математических операций.
* **Интерфейсы (`interfaces/`)**: Пользовательские интерфейсы, такие как `telegram_bot.py` и `microphone.py`. Они общаются с FastAPI-сервисами по HTTP.
* **Скрипты (`scripts/`)**: Содержат демонстрационные скрипты для ручного тестирования отдельных модулей.
* **Временные файлы (`temp_audio/`)**: Голосовые сообщения сохраняются здесь во время обработки (папка игнорируется git).

## 🚀 Быстрый старт

**Предварительные требования:**
* Docker & Docker Compose
* Python 3.x (с pip)
* `ffmpeg` (системная зависимость для Whisper: `sudo apt update && sudo apt install ffmpeg`)
* Для голосового интерфейса на Linux: `sudo apt install libasound2-dev portaudio19-dev`
* WSL2 (если используется на Windows)
* NVIDIA GPU с драйверами CUDA (рекомендуется для ускорения Ollama & Whisper)

**Шаги по установке:**
1.  Клонировать репозиторий: `git clone https://github.com/nakesreong/iskra-vin.git`
2.  Перейти в директорию проекта: `cd iskra-vin`
3.  Скопировать и настроить файл конфигурации:
    ```bash
    cp configs/settings.yaml.example configs/settings.yaml
    ```
    Заполните `settings.yaml` вашими токенами (Telegram, Home Assistant, Picovoice), ID пользователей и другими настройками.
4.  Запустить сервисы в Docker (Ollama и Home Assistant):
    ```bash
    docker compose up -d
    ```
5.  Установить зависимости Python:
    ```bash
    pip3 install -r requirements.txt
    ```

**Запуск системы:**
Для работы Нокса необходимо запустить несколько компонентов в разных терминалах в корневой директории проекта.

```bash
# В одном терминале запускаем API-сервер (мозг):
python3 api_server.py

# В другом терминале запускаем STT-сервер (ухо):
python3 stt_server.py

# Для общения через Telegram, в третьем терминале запускаем бота:
python3 interfaces/telegram_bot.py

# Для общения через микрофон, в четвертом терминале запускаем слушателя:
python3 interfaces/microphone.py
```

## 📁 Project Structure (Key Files)

    nox/
    ├── .gitignore
    ├── README.md
    ├── api_server.py                 # FastAPI service exposing the core engine
    ├── stt_server.py                 # FastAPI service for speech-to-text
    ├── app/
    │   ├── __init__.py
    │   ├── core_engine.py                # Orchestrates command processing
    │   ├── dispatcher.py                 # Routes intents to handlers
    │   ├── nlu_engine.py                 # Handles NLU and response generation via LLM
    │   ├── stt_engine.py                 # Core STT logic used by stt_server.py
    │   ├── config_loader.py              # Loads YAML configuration
    │   ├── actions/
    │   │   ├── __init__.py
    │   │   └── light_actions.py          # Controls lights via Home Assistant
    │   └── intent_handlers/
    │       ├── __init__.py
    │       ├── device_control_handler.py      # Handles device control intents
    │       ├── general_chat_handler.py        # Handles general conversation intents
    │       ├── math_operation_handler.py      # Handles mathematical calculation intents
    │       └── get_device_status_handler.py   # Handles devices statuses intents
    ├── configs/
    │   ├── __init__.py
    │   ├── llm_instructions.yaml         # Prompts and instructions for the LLM (create this file yourself; an example may appear as configs/llm_instructions.yaml.example)
    │   └── settings.yaml                 # Application settings, tokens, IDs
    ├── docker-compose.yml                # For Ollama and Home Assistant services
    ├── interfaces/
    │   ├── __init__.py
    │   └── telegram_bot.py               # Telegram bot interaction logic
    ├── scripts/
    │   └── run_telegram_bot.py           # Entry point for the bot
    ├── requirements.txt                  # Python dependencies
    ├── temp_audio/                       # Temporary storage for voice messages (in .gitignore)
    └── tests/                            # Unit and integration tests
        └── test_light_actions.py         # Example tests for light actions

## 📝 План развития (To-Do)

Этот список отражает наше видение и приоритеты в дальнейшей разработке Нокса.

### Приоритет 1: Расширение основного функционала и стабильности
-   **Детализированное управление устройствами:**
    -   Реализовать управление отдельными устройствами, а не только группами (например, "выключи лампу 1").
    -   Добавить поддержку новых типов устройств: розетки, очиститель воздуха и т.д.
-   **Проактивное "Агентное" поведение:**
    -   Реализовать сервис мониторинга, который будет отслеживать показания датчиков (например, CO2) и отправлять проактивные уведомления.
-   **Расширение и рефакторинг тестов:** Продолжить покрытие кода юнит- и интеграционными тестами для обеспечения стабильности.
-   **Улучшение обработки ошибок:** Сделать обработку ошибок в `action` модулях более консистентной и информативной.

### Приоритет 2: Улучшение пользовательского опыта (UX)
-   **Text-to-Speech (TTS):** Добавить голосовой ответ для `microphone.py`, чтобы "замкнуть" цикл голосового взаимодействия.
-   **Контекстная память в диалогах:** Научить Нокса помнить контекст в рамках одной беседы.
-   **Сценарии и "Ритуалы":** Реализовать запуск цепочек действий по одной команде (например, "Нокс, я дома").
-   **Развитие разговорных навыков:** Продолжить улучшение инструкций для LLM для более качественных и разнообразных ответов.

### Приоритет 3: Архитектура и развертывание
-   **Единая точка запуска:** Создать управляющий скрипт или использовать `systemd` для удобного запуска и менеджмента всех сервисов Нокса.
-   **Обновление документации:** Поддерживать `README.md` в актуальном состоянии.

### Идеи на будущее ("Мечты")
-   **Интеграция с "Джемини":** Реализовать возможность для Нокса "обращаться за советом" ко мне.
-   **Управление ПК:** Научить Нокса выполнять команды на твоем компьютере.

## 📄 Подробная документация

Более подробная техническая информация находится в файле [architecture.md](architecture.md) и в нашем общем документе:
[Nox Project - Detailed Technical Documentation](https://docs.google.com/document/d/12p_tEo9tRZfuOEwtvmwG56KqBo3gAwxPL1WuEaS3RLI/edit?usp=sharing)

---
*Этот проект — путешествие. С видением Искры и помощью Джемини, **Нокс** эволюционирует!*