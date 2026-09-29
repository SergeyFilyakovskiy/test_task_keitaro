.PHONY: up down restart logs clean shell psql migrations migrate ruff test build ps

# Поднять всё с билдом
up:
	docker compose -f docker-compose.dev.yml up -d --build

# Остановить (данные остаются)
down:
	docker compose -f docker-compose.dev.yml down

# Перезапустить
restart: down up

# Логи
logs:
	docker compose -f docker-compose.dev.yml logs -f

# Логи конкретного сервиса
logs-app:
	docker compose -f docker-compose.dev.yml logs -f app

# Полная очистка: стоп + удаление volumes (бд удалится!)
clean:
	docker compose -f docker-compose.dev.yml down -v --remove-orphans

# Залезть внутрь контейнера
shell:
	docker compose -f docker-compose.dev.yml exec app bash

# Подключиться к postgres
psql:
	docker compose -f docker-compose.dev.yml exec db psql -U postgres -d test_task_keitaro

# Создать новую миграцию (autogenerate)
migrations:
	docker compose -f docker-compose.dev.yml exec app alembic revision --autogenerate -m "$(msg)"

# Применить миграции вручную
migrate:
	docker compose -f docker-compose.dev.yml exec app alembic upgrade head

# Откатить последнюю миграцию
downgrade:
	docker compose -f docker-compose.dev.yml exec app alembic downgrade -1

# Линтер
ruff:
	docker compose -f docker-compose.dev.yml exec app ruff check .

# Тесты
test:
	docker compose -f docker-compose.dev.yml exec app pytest -v

# Пересобрать образ
build:
	docker compose -f docker-compose.dev.yml build --no-cache

# Статус контейнеров
ps:
	docker compose -f docker-compose.dev.yml ps

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  make up          - запустить всё (с билдом)"
	@echo "  make down        - остановить"
	@echo "  make restart     - перезапустить"
	@echo "  make logs        - логи всех сервисов"
	@echo "  make clean       - удалить контейнеры + volumes"
	@echo "  make shell       - shell внутри app"
	@echo "  make psql        - psql консоль"
	@echo "  make migrations msg='...' - создать миграцию"
	@echo "  make test        - запустить тесты"