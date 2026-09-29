# test_task_keitaro

Обёртка над **Keitaro Admin API v1**: создаватор кампаний и редактор потоков
(офферы, веса, pin, синхронизация с Keitaro).

Тестовое задание на позицию Middle Python Developer.

---

## Что реализовано

### Часть 1. Создаватор кампаний
`POST /api/v1/campaigns` принимает `name`, `geo` (список кодов стран), `offer_id` и создаёт в Keitaro кампанию:
- с настроенными **доменом, группой и источником** (группа/источник создаются автоматически, если их нет в Keitaro);
- с **двумя потоками**:
  - **Flow 1** (`forced`): фильтр `country accept [geo]` → редирект на `https://google.com`;
  - **Flow 2** (`default`): ротация на выбранный оффер (стартовый вес 100%).

### Часть 2. Редактор существующей кампании
- **Fetch streams from KT** — синхронизация потоков и офферов из Keitaro;
- **Add / Remove / Bring back** офферов с автоматическим пересчётом весов;
- **Pin / Unpin** фиксированных весов;
- **Push to KT** — применение локальных изменений в Keitaro;
- **Cancel** — откат локальных изменений к последнему синку;
- визуальные состояния: «жёлтый» поток (незапушенные изменения), серые офферы (удалены в Keitaro), офферы в истории (локально удалённые).

---

## Стек

| Слой | Технологии |
|---|---|
| Backend | Python 3.14, FastAPI, SQLAlchemy 2.0 (async, asyncpg), Alembic, pydantic-settings, httpx |
| БД | PostgreSQL 16 |
| Пакетный менеджер | uv |
| Frontend | Jinja2 + vanilla JS + jQuery UI (autocomplete) + Tailwind CDN (без сборки и без отдельного контейнера) |
| Инфраструктура | Docker Compose (dev), Makefile |

---

## Быстрый старт

Требования: `docker`, `docker compose`, `make`.

1. Склонируй репозиторий:
   ```bash
   git clone <repo-url> && cd test_task_keitaro
   ```

2. Создай `.env` в корне проекта:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   POSTGRES_AUTH_DB=test_task_keitaro

   KEITARO_API_URL=https://<your-tracker>/admin_api/v1
   KEITARO_API_KEY=<your-api-key>

   # Опционально: дефолты создаватора кампаний
   KEITARO_DEFAULT_DOMAIN_ID=
   KEITARO_DEFAULT_GROUP_NAME=FORTESTS
   KEITARO_DEFAULT_SOURCE_NAME=FORTESTS
   ```

3. Подними проект:

   ```bash
   make up

   ```

   При старте контейнера `entrypoint.sh` дожидается готовности PostgreSQL
   и сам применяет миграции (`alembic upgrade head`).

4. Открой:
   - UI: http://localhost:8000
   - Swagger: http://localhost:8000/api/docs

---

## Makefile

| Команда | Действие |
|---|---|
| `make up` | Поднять контейнеры с пересборкой |
| `make down` | Остановить (данные БД сохраняются) |
| `make restart` | Перезапустить |
| `make logs` | Логи всех сервисов |
| `make clean` | Удалить контейнеры и volumes (БД сбрасывается) |
| `make shell` | Shell внутри контейнера app |
| `make psql` | psql-консоль PostgreSQL |
| `make migrations msg="..."` | Создать миграцию (autogenerate) |
| `make migrate` | Применить миграции вручную |
| `make downgrade` | Откатить последнюю миграцию |
| `make test` | Запустить pytest |
| `make ruff` | Линтер |
| `make build` | Пересборка образа без кэша |

---

## Структура проекта

```

.
├── app
│   ├── api
│   │   └── v1
│   │       ├── endpoints        # HTTP-роуты (campaigns, flows, offers, pages, debug)
│   │       ├── schemas          # Pydantic DTO
│   │       └── routers.py
│   ├── core
│   │   ├── config.py            # pydantic-settings конфиг (.env)
│   │   └── dependencies.py      # DI: сессия БД (unit-of-work), Keitaro-клиент
│   ├── infrastructure
│   │   ├── db
│   │   │   ├── models.py        # SQLAlchemy модели: Campaign, Flow, FlowOffer
│   │   │   ├── repositories     # Тонкий слой над SQLAlchemy
│   │   │   └── session.py       # async engine / sessionmaker
│   │   └── external
│   │       └── keitaro_client.py# httpx-клиент Keitaro Admin API v1
│   ├── migrations               # Alembic (env.py, versions/)
│   ├── services                 # Бизнес-логика
│   │   ├── campaign_service.py  # Часть 1: создание кампании
│   │   ├── flow_service.py      # Часть 2: fetch/push/cancel/мутации офферов
│   │   ├── weight_service.py    # Математика весов (чистая функция)
│   │   └── offer_service.py     # Поиск офферов для автокомплита
│   ├── static                   # js/css фронта
│   ├── templates                # Jinja2-шаблоны страниц
│   └── main.py                  # Точка входа + обработчики ошибок
├── docker
│   └── entrypoint.sh            # wait postgres → alembic upgrade head → uvicorn
├── tests
│   └── test_weight_service.py   # Юнит-тесты пересчёта весов
├── docker-compose.dev.yml
├── Dockerfile
├── Makefile
├── alembic.ini
└── pyproject.toml

```

---

## API

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/v1/campaigns` | Создать кампанию (name, geo, offer_id) |
| GET | `/api/v1/campaigns` | Список кампаний |
| GET | `/api/v1/campaigns/{id}` | Кампания + потоки + офферы (для редактора) |
| POST | `/api/v1/campaigns/{id}/fetch` | Fetch streams from KT (409 при dirty) |
| POST | `/api/v1/flows/{flow_id}/push` | Push to KT |
| POST | `/api/v1/flows/{flow_id}/cancel` | Откат к последнему синку |
| POST | `/api/v1/flows/{flow_id}/offers` | Добавить оффер |
| DELETE | `/api/v1/flows/{flow_id}/offers/{offer_id}` | Удалить оффер |
| POST | `/api/v1/flows/{flow_id}/offers/{offer_id}/bring_back` | Восстановить оффер |
| PUT | `/api/v1/flows/{flow_id}/offers/{offer_id}/pin` | Запинить вес |
| DELETE | `/api/v1/flows/{flow_id}/offers/{offer_id}/pin` | Снять пин |
| GET | `/api/v1/offers/search?q=` | Автокомплит офферов (прокси в Keitaro) |
| GET | `/api/v1/debug/references` | Dev-дамп справочников Keitaro (фильтры, actions, schemas) |

Коды ошибок домена: `404` — не найдено, `409` — есть незапушенные изменения,
`400` — нарушение бизнес-правил, `502` — ошибка Keitaro API.

---

## Доменная логика

### Состояния потоков и офферов
- **Поток «жёлтый»** (`is_synced = false`) — есть локальные изменения, не запушенные в Keitaro.
  Появляется после любой мутации офферов; сбрасывается после `push` или `cancel`.
- **Fetch при dirty** запрещён: возвращается `409` с подсказкой «запушь или откати».
- **Серый оффер** (`is_deleted_in_keitaro = true`) — оффер отсутствует в Keitaro
  (удалён внешне или запушен как удалённый). Отображается с кнопкой `bring back`.
- **Оффер в истории** (`is_active = false`) — локально удалён, участвует в `bring back`.
- Потоки **без офферов** (например, Flow 1 с редиректом) отображаются как факт
  существования без деталей (фильтры/редирект не раскрываются).

### Синхронизация
- **Fetch**: потоки и веса берутся из Keitaro **как есть, без пересчёта**.
  Если в Keitaro удалили оффер — остальные сохраняют свои веса (сумма может стать ≠ 100,
  это подсвечивается в UI), удалённый становится серым.
- **Push**: `PUT /streams/{id}` с активными офферами и их весами; после успеха
  обновляется снапшот (`last_synced_snapshot`) и поток становится синхронизированным.
- **Cancel**: офферы потока откатываются к снапшоту последнего синка.

### Алгоритм весов
- Сумма весов активных офферов = **100%**.
- Запиненные офферы получают фиксированный вес.
- Остаток (`100 - сумма_пинов`) делится между незапиненными:
  `base = остаток // N`, **целый остаток от деления отдаётся первому по порядку**.
- Примеры: 3 оффера → `34/33/33`; пин 25% при трёх → `25/38/37`; 7 офферов → `16/14/14/14/14/14/14`.
- Пересчёт запускают: add, remove, bring back, pin, unpin. Fetch пересчёт НЕ запускает.
- Валидация: минимум один активный оффер; сумма пинов не больше 100.

### Константы Keitaro
Имена схем/действий/фильтров вынесены в `app/services/keitaro_consts.py`.
Проверить актуальные значения на вашем трекере можно dev-ручкой:
```bash
curl -s localhost:8000/api/v1/debug/references | jq
```

---

## Тесты

```bash
make test
# или внутри контейнера
pytest tests/ -v
```

Покрыта ключевая математика весов: равное распределение, остаток первому,
пин/анпин, add/remove/bring back, валидации.

---

## Заметки и ограничения
- Frontend сознательно без сборки и без отдельного контейнера: Jinja2-шаблоны +
  статика раздаются самим FastAPI, интерактив — vanilla JS + jQuery UI autocomplete.
- Keitaro — источник истины для потоков; наша БД хранит локальное рабочее состояние,
  снапшоты синков и историю офферов (для bring back).
- Ошибки Keitaro API проксируются как `502` с текстом ошибки в `detail`.

---

## Известные ограничения и возможные улучшения

Ниже — осознанные компромиссы, сделанные в рамках тестового задания.
В production-версии каждое из этих мест требует доработки.

### 1. Отсутствие распределённой транзакции между Keitaro и нашей БД

При создании кампании (`POST /api/v1/campaigns`) мы последовательно:
1. создаём кампанию в Keitaro (`POST /admin_api/v1/campaigns`);
2. создаём два потока в Keitaro;
3. пишем сущности в свою БД.

Если шаг 3 упадёт (сетевой сбой, конфликт в БД), в Keitaro останутся "висящие"
кампания и потоки без соответствия в нашем приложении.

**Варианты решения в production:**
- **Saga / компенсирующие действия**: при ошибке на шаге 3 удалить созданные
  сущности из Keitaro (`DELETE /campaigns/{id}`, `DELETE /streams/{id}`).
- **Outbox-паттерн**: сначала писать событие `campaign_created` в локальную
  таблицу с `status=pending`, затем асинхронный воркер создаёт сущности
  в Keitaro и обновляет статус. Это даёт idempotency и гарантирует eventual consistency.
- **Two-phase commit через idempotency key**: генерировать детерминированный
  `alias`/`external_id` на стороне клиента, чтобы повторные попытки создания
  возвращали уже существующую сущность в Keitaro, а не дубликат.

### 2. Загрузка всех офферов для автокомплита

`OfferService.search` получает весь список офферов через `GET /offers`
и фильтрует в Python. При большом количестве офферов (1000+) это неэффективно.

**Решение:**
- in-memory кэш с TTL 5–10 минут (`cachetools.TTLCache` или `redis`);
- либо server-side фильтрация, если Keitaro её поддерживает в будущих версиях API.

### 3. Снапшоты и состояние relationship

При создании офферов через `bulk_create` мы строим снапшот
(`last_synced_snapshot`) **из только что созданных ORM-объектов**, а не
через `session.refresh(flow, ["offers"])`. Это надёжнее и быстрее:
не зависит от того, что SQLAlchemy успел подгрузить relationship,
и экономит один SELECT.

Хелпер `build_snapshot_from_rows` в `app/services/snapshots.py` решает эту задачу.

### 4. Отсутствие retry-логики для Keitaro API

Сетевые ошибки (таймауты, 502/503 от Keitaro) приводят к немедленному `502`
пользователю. В production нужен exponential backoff + retry для идемпотентных
операций (GET, PUT с детерминированным телом).
