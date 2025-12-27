.PHONY: up ps logs down help shell dev

PROJECT_DIR := DBCV
COMPOSE := docker-compose -f docker-compose.dev.yml --env-file env.dev
SERVICE ?= backend

help:
	@echo "Available targets:"
	@echo "  up    - Start dev stack"
	@echo "  ps    - Show services status"
	@echo "  logs  - Tail backend logs"
	@echo "  down  - Stop and remove stack"
	@echo "  dev   - Start stack in foreground (stream logs)"
	@echo "  shell - Open interactive shell in a service (default: backend)"

up:
	$(COMPOSE) up -d

dev:
	$(COMPOSE) up

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f backend

shell:
	$(COMPOSE) exec $(SERVICE) bash || $(COMPOSE) exec $(SERVICE) sh

down:
	$(COMPOSE) down

re: down dev