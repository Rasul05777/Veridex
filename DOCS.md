# Verilab: текущая документация проекта

## 1. Что это за проект

`verilab` - MVP исследовательского AI-агента для учебного security assessment в контролируемой среде.

Проект принимает цель и target через HTTP API, проверяет target по allowlist, запускает LangGraph-граф агента, вызывает LLM через LiteLLM/OpenRouter, а команды инструментов выполняет внутри Docker-контейнеров.

Текущий проект не содержит жестко заданного набора проверок вроде `check_xss()` или `check_sqli()`. Набор действий выбирает LLM на основании `goal`, `target`, плана и доступных tools.

## 2. Что проект умеет сейчас

На текущий момент реализовано:

- FastAPI API для создания задачи и просмотра результата.
- Scope Guard: target должен быть в `VERILAB_ALLOWED_TARGETS`.
- Фоновая очередь задач на `asyncio.Queue`.
- LangGraph-граф из узлов `plan`, `reason`, `tool_call`, `verify`.
- LiteLLM-адаптер для вызова модели, сейчас настроен под OpenRouter.
- Реестр LLM-tools: `execute_command`, `list_backends`, `report_finding`.
- Docker gateway для запуска CLI-инструментов в контейнерах.
- SQLite-база `data/verilab.db` для задач и контекста.
- Запись трассировки: `thought`, `action`, `observation`, `finding`.
- Базовые unit-тесты для config, DB, API, tools, graph routes и agent-модулей.

Чего пока нет:

- Детерминированных verification functions по каждой подзадаче.
- Настоящего DAG-плана, сейчас planner возвращает `list[str]`.
- Human approval-gate перед опасными действиями.
- Проверки target внутри shell-команды.
- Подключенного rate-limit на выполнение tools.
- LangGraph SQLite checkpointer.
- Long-term memory и RAG.
- Жесткой политики "какие уязвимости проверять всегда".

## 3. Быстрый запуск

### 3.1 Настройки

Основные настройки лежат в `.env`.

Пример:

```dotenv
OPENROUTER_API_KEY=sk-or-v1-...
VERILAB_LLM_MODEL=openrouter/qwen/qwen3.7-max
VERILAB_ALLOWED_TARGETS=http://testphp.vulnweb.com,https://example.com
VERILAB_DB_PATH=data/verilab.db
VERILAB_MAX_ITERATIONS=10
```

Важно: target в запросе должен совпадать со строкой из `VERILAB_ALLOWED_TARGETS` буквально.

Например, если разрешено:

```dotenv
https://example.com
```

то это не то же самое, что:

```dotenv
http://example.com
https://example.com/
```

### 3.2 Запуск контейнеров

```bash
docker compose up -d
docker compose ps
```

Ожидаемые контейнеры:

- `verilab-kali`
- `verilab-nmap`
- `verilab-nuclei`
- `verilab-semgrep`
- `verilab-trufflehog`

### 3.3 Запуск API

```bash
python -m src
```

Команда запускает `src/__main__.py`, а он поднимает Uvicorn с приложением `src.api:app` на порту `8000`.

### 3.4 Создание задачи

```bash
curl -X POST http://127.0.0.1:8000/task \
  -H 'Content-Type: application/json' \
  -d '{"goal":"Inspect the allowed laboratory target and report observations","target":"https://example.com"}'
```

Ответ:

```json
{"task_id": 1}
```

### 3.5 Проверка статуса

```bash
curl http://127.0.0.1:8000/task/1
```

Возможные статусы:

- `queued`
- `running`
- `done`
- `error`

### 3.6 Просмотр трассировки

```bash
curl -s http://127.0.0.1:8000/task/1/context | python -m json.tool
```

В контексте можно увидеть:

- `thought` - рассуждение модели.
- `action` - какой tool вызван и с какими аргументами.
- `observation` - результат выполнения tool.
- `finding` - зафиксированная находка из `report_finding`.

## 4. Архитектура на верхнем уровне

Поток работы:

```text
Client
  |
  v
FastAPI /task
  |
  v
Scope Guard
  |
  v
SQLite task + asyncio.Queue
  |
  v
Worker
  |
  v
LangGraph:
  plan -> reason -> tool_call -> reason -> verify -> END
  |
  v
SQLite context
```

LLM не вызывает Docker напрямую. Она вызывает tools в формате function calling. Код графа принимает tool call, проверяет allowlist tool-ов и только потом вызывает gateway.

## 5. Структура проекта

```text
.
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── DOCS.md
├── data/
│   └── verilab.db
├── labs/
│   ├── kali/Dockerfile
│   ├── nmap/Dockerfile
│   ├── nuclei/Dockerfile
│   ├── semgrep/Dockerfile
│   └── trufflehog/Dockerfile
├── src/
│   ├── __main__.py
│   ├── api.py
│   ├── agent/
│   ├── core/
│   ├── graph/
│   ├── memory/
│   ├── safety/
│   └── tools/
└── tests/
```

`data/verilab.db` - runtime-файл SQLite. Он создается приложением и хранит локальную историю задач.

## 6. API

### `POST /task`

Файл: `src/api.py`

Создает новую задачу.

Тело запроса:

```json
{
  "goal": "Inspect target",
  "target": "https://example.com"
}
```

Что происходит:

1. `target` проверяется через `check_target()`.
2. Создается запись в SQLite через `create_task()`.
3. Задача кладется в `_queue`.
4. Возвращается `task_id`.

### `GET /task/{task_id}`

Возвращает краткий статус задачи:

```json
{
  "task_id": 1,
  "goal": "...",
  "target": "...",
  "status": "done",
  "findings": []
}
```

`findings` берутся из таблицы `context`, где `type == "finding"`.

### `GET /task/{task_id}/context`

Возвращает полный журнал выполнения задачи из SQLite.

Это главный endpoint для понимания, что реально делал агент.

## 7. LangGraph

LangGraph находится в `src/graph/`.

### `src/graph/state.py`

Описывает состояние графа:

```python
class AgentState(TypedDict):
    task_id: int
    goal: str
    target: str
    plan: list[str]
    messages: Annotated[list[dict], operator.add]
    findings: Annotated[list[dict], operator.add]
    verified: bool
    iterations: int
    max_iterations: int
```

Поля `messages` и `findings` помечены через `operator.add`. Это значит, что LangGraph добавляет новые элементы к списку, а не заменяет список целиком.

### `src/graph/build.py`

Собирает граф:

```text
plan -> reason -> tool_call -> reason
              \-> verify -> END или reason
```

Узлы:

- `_plan_node()` - строит план и создает первое user-сообщение.
- `_reason_node()` - вызывает reasoner.
- `_tool_call_node()` - выполняет tool calls.
- `_verify_node()` - вызывает verifier.

### `src/graph/routes.py`

Содержит условные переходы.

После `reason`:

- если достигнут `max_iterations`, перейти в `verify`;
- если последний ответ LLM содержит `tool_calls`, перейти в `tool_call`;
- иначе перейти в `verify`.

После `verify`:

- если `verified == True`, завершить;
- если достигнут `max_iterations`, завершить;
- иначе вернуться в `reason`.

## 8. Agent-модули

### `src/agent/planner.py`

Функция:

```python
plan(goal: str, target: str) -> list[str]
```

Назначение:

- отправляет в LLM цель и target;
- просит вернуть JSON-массив строк;
- парсит ответ;
- при невалидном JSON возвращает пустой список.

Сейчас это не DAG, а простой список подзадач.

### `src/agent/reasoner.py`

Функция:

```python
reason(state: AgentState) -> dict
```

Назначение:

- формирует system prompt с планом;
- передает историю `state["messages"]`;
- дает LLM список tools из `to_openai_tools()`;
- возвращает новое assistant-сообщение;
- увеличивает `iterations`.

Именно reasoner решает, вызывать tool или идти к завершению.

### `src/agent/verifier.py`

Функция:

```python
verify(findings: list[dict], goal: str) -> dict
```

Назначение:

- отправляет goal и findings в LLM;
- просит JSON вида:

```json
{"verified": true, "gaps": ""}
```

- если JSON сломан, возвращает:

```python
{"verified": False, "gaps": "Verifier returned non-JSON response, retrying"}
```

Важно: сейчас verifier - это LLM-оценка, а не детерминированная verification function.

## 9. Tools

Tools описаны в `src/tools/registry.py`.

### `Tool`

Dataclass:

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
```

### `TOOL_REGISTRY`

Сейчас зарегистрированы 3 tool-а.

#### `execute_command`

Позволяет LLM попросить выполнить shell-команду в одном из Docker backend-ов.

Параметры:

- `command`
- `backend`
- `timeout`

Backend может быть:

- `kali`
- `nuclei`
- `nmap`
- `semgrep`
- `trufflehog`

#### `list_backends`

Возвращает список доступных backend-ов и их назначение.

#### `report_finding`

Записывает найденное наблюдение или проблему.

Поля:

- `severity`: `critical`, `high`, `medium`, `low`, `info`
- `title`
- `description`
- `tool`

### `to_openai_tools()`

Преобразует локальный реестр tools в формат function calling, понятный LLM API.

## 10. Tool Gateway

Файл: `src/tools/gateway.py`

### `BACKENDS`

Описывает Docker-контейнеры:

| Backend | Контейнер | Назначение |
|---|---|---|
| `kali` | `verilab-kali` | Общий pentest-набор |
| `nuclei` | `verilab-nuclei` | CVE/template scanner |
| `nmap` | `verilab-nmap` | Сканер портов |
| `semgrep` | `verilab-semgrep` | SAST |
| `trufflehog` | `verilab-trufflehog` | Поиск секретов |

### `execute(command, backend="kali", timeout=300)`

Выполняет:

```bash
docker exec <container> <shell> -c <command>
```

И возвращает:

```python
stdout + stderr
```

Если backend неизвестен, возвращает строку с ошибкой.

### `list_backends()`

Возвращает описание backend-ов без внутренних технических полей.

## 11. Safety

### `src/safety/scope_guard.py`

Функция:

```python
check_target(target: str, allowed: list[str]) -> None
```

Если target не входит в allowlist, выбрасывает `ScopeViolation`.

Где используется:

```python
POST /task
```

То есть задача не попадет в очередь, если target не разрешен.

Ограничение: сейчас Scope Guard проверяет только поле `target` в API-запросе. Он не анализирует shell-команду внутри `execute_command`.

### `src/safety/gates.py`

#### `AllowedToolsGate`

Проверяет, что имя tool-а входит в allowlist.

В графе разрешены:

```python
{"execute_command", "list_backends", "report_finding"}
```

#### `RateLimiter`

Класс rate limiter уже написан, но сейчас не подключен к `gateway.execute()` или `_tool_call_node()`.

## 12. Core

### `src/core/config.py`

Класс `Settings` читает настройки из `.env`.

Основные поля:

- `openrouter_api_key`
- `llm_model`
- `allowed_targets`
- `db_path`
- `max_iterations`

`allowed_targets_list` превращает строку:

```text
https://a.com,https://b.com
```

в список:

```python
["https://a.com", "https://b.com"]
```

### `src/core/llm.py`

Функция:

```python
chat(messages: list[dict], tools: list[dict] | None = None) -> dict
```

Назначение:

- выставляет `OPENROUTER_API_KEY`;
- вызывает `litellm.completion()`;
- передает `model`, `messages`, optional `tools`;
- нормализует ответ LLM в обычный dict.

Если модель вернула tool calls, они сохраняются в формате:

```json
{
  "id": "...",
  "type": "function",
  "function": {
    "name": "...",
    "arguments": "..."
  }
}
```

### `src/core/db.py`

Создает и использует SQLite-базу.

Таблица `tasks`:

- `id`
- `goal`
- `target`
- `status`
- `created_at`

Таблица `context`:

- `id`
- `task_id`
- `type`
- `message`
- `agent`
- `timestamp`

Функции:

- `init_db()`
- `create_task()`
- `update_task_status()`
- `save_context()`
- `get_task()`
- `get_context()`

### `src/core/logging.py`

Настраивает JSON-логи через `structlog`.

Пример события:

```json
{"task_id": 1, "event": "task done", "level": "info", "timestamp": "..."}
```

## 13. Memory

Файл: `src/memory/short_term.py`

Есть класс `Scratchpad`:

- `set(task_id, key, value)`
- `get(task_id, key, default=None)`
- `clear(task_id)`

Это потокобезопасная in-memory память на базе `dict` и `Lock`.

Ограничение: сейчас `scratchpad` нигде не используется в рабочем графе.

## 14. Docker labs

### `docker-compose.yml`

Поднимает пять сервисов в сети `pentest-net`.

Все сервисы запускаются с:

```yaml
entrypoint: ["tail", "-f", "/dev/null"]
```

Это сделано, чтобы контейнеры постоянно жили, а команды выполнялись через `docker exec`.

### `labs/kali/Dockerfile`

Устанавливает:

- `nikto`
- `sqlmap`
- `gobuster`
- `ffuf`
- `hydra`
- `whois`
- `curl`
- `wget`
- `dnsutils`
- `nmap`
- `python3`
- `python3-pip`
- `ca-certificates`

### `labs/nmap/Dockerfile`

Минимальный Ubuntu-контейнер с `nmap`.

### `labs/nuclei/Dockerfile`

Контейнер ProjectDiscovery Nuclei. При сборке пытается обновить templates.

### `labs/semgrep/Dockerfile`

Контейнер Semgrep.

### `labs/trufflehog/Dockerfile`

Контейнер TruffleHog для поиска секретов.

## 15. Что именно проверяет проект

Сейчас нет фиксированного списка уязвимостей.

Проект потенциально может проверять то, что LLM решит проверить доступными инструментами:

| Категория | Возможный инструмент |
|---|---|
| HTTP-заголовки | `curl`, `nikto`, `nuclei` |
| Открытые порты | `nmap` |
| Версии сервисов | `nmap -sV` |
| Известные CVE/misconfig | `nuclei` |
| Базовые web-проблемы | `nikto` |
| SQL injection | `sqlmap`, если LLM его вызовет |
| Директории и файлы | `gobuster`, `ffuf` |
| Секреты в файлах/репозиториях | `trufflehog` |
| Статический анализ кода | `semgrep` |

Чтобы понять, что было проверено в конкретной задаче, нужно смотреть:

```bash
curl -s http://127.0.0.1:8000/task/<id>/context | python -m json.tool
```

И искать записи:

```json
{
  "type": "action"
}
```

В `message` будет JSON с полями:

- `tool_call_id`
- `tool`
- `arguments`

## 16. Как задача завершается

Задача завершается, если:

- verifier вернул `verified == True`;
- или достигнут `VERILAB_MAX_ITERATIONS`;
- или worker поймал ошибку и поставил статус `error`.

Если все прошло нормально, `_run_agent()` ставит:

```python
status = "done"
```

## 17. Тесты

Каталог: `tests/`

Покрывают:

- настройки;
- SQLite DB;
- Scope Guard;
- gates;
- tools registry;
- Docker gateway через mock;
- planner;
- reasoner;
- verifier;
- graph routes;
- API.

Запуск:

```bash
python -m pytest -q
```

Если `pytest` не установлен:

```bash
uv sync --extra dev
python -m pytest -q
```

## 18. Важные текущие ограничения

### 18.1 Shell-команда не проверяется по scope

API проверяет `target`, но если LLM сформирует команду с другим URL, текущий gateway это не остановит.

Нужно добавить проверку на уровне `execute_command`.

### 18.2 Нет approval-gate

Сейчас `execute_command` выполняется сразу после tool call.

Для production-like безопасности нужен HITL:

```text
LLM wants action -> safety review -> human approve/deny -> execute
```

### 18.3 RateLimiter не подключен

Класс есть, но в runtime не используется.

### 18.4 Verifier не детерминированный

Сейчас verifier - это запрос к LLM. По ТЗ verification functions должны быть кодом.

### 18.5 Нет checkpointer

SQLite используется для задач и контекста, но не как LangGraph checkpointer.

### 18.6 Runtime DB лежит в репозитории

`data/verilab.db` - локальный артефакт. Его обычно не стоит коммитить.

## 19. Рекомендуемые следующие шаги

1. Добавить проверку scope внутри `execute_command`.
2. Подключить `RateLimiter` в `_tool_call_node()`.
3. Добавить approval-gate для опасных tools.
4. Сделать deterministic fake LLM для запуска без API-ключей.
5. Перевести planner с `list[str]` на DAG.
6. Реализовать verification functions как код.
7. Добавить отдельную таблицу `findings`.
8. Подключить LangGraph SQLite checkpointer.
9. Добавить `data/*.db` в `.gitignore`.
10. Добавить safe profiles для tools: passive, light, full-lab.
