# Makefile for Django Application with Docker-Compose Command Style

APP_ENV ?= development
APP_VENV_PATH ?= .venv

ENV_FILE = src/.env
ENV_DOCKER_COMPOSE_FILE = deployments/$(APP_ENV)/docker-compose.yml

PIP = $(APP_VENV_PATH)/bin/pip
VENV = $(APP_VENV_PATH)/bin/activate
PYTHON = $(APP_VENV_PATH)/bin/python


# Docker Commands
up:
	@# Start all Docker services
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) up --build

up-d:
	@# Start all Docker services
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) up -d --build

down:
	@# Stop all Docker services
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) down

start:
	@# Start a specific Docker service
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) start $(SERVICE)

stop:
	@# Stop a specific Docker service
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) stop $(SERVICE)

restart:
	@# Restart a specific Docker service
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) restart $(SERVICE)

logs:
	@# View logs for a specific service
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) logs -f $(SERVICE)

exec:
	@# Execute a command in a running service
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) exec $(SERVICE) $(COMMAND)

build:
	@# Build or rebuild Docker services
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) build $(SERVICE)

shell:
	docker compose -f $(ENV_DOCKER_COMPOSE_FILE) exec api python3 src/manage.py shell_plus


# Django-Specific Commands

install-dev: venv
	: # Activate virtual environment and install requirements inside
	. $(VENV) && $(PYTHON) -m pip install -r requirements/development.txt

install: venv
	: # Activate virtual environment and install requirements inside
	. $(VENV) && $(PYTHON) -m pip install -r requirements.txt

venv:
	: # Create virtual environment if it doesn't exist
	test -d .venv || $(PYTHON) -m venv --prompt="v" .venv

runserver: install-dev
	@# Run Django server
	. $(VENV) && $(PYTHON) src/manage.py runserver

createsuperuser: venv
	@# Create a superuser
	. $(VENV) && $(PYTHON) src/manage.py createsuperuser

makemigrations: venv
	@# Make database migrations
	. $(VENV) && $(PYTHON) src/manage.py makemigrations

migrate: venv
	@# Apply database migrations
	. $(VENV) && $(PYTHON) src/manage.py migrate

loaddata: venv
	@# Load data from fixtures
	. $(VENV) && $(PYTHON) src/manage.py loaddata src/*/fixtures/*.json

seed: venv
	@# Seed the database with fake data
	. $(VENV) && $(PYTHON) src/manage.py runscript seeding

lint:
	@# Lint all files
	. $(VENV) && ruff check .

lint-fix:
	@# Auto-fix lint errors
	. $(VENV) && ruff check --fix .

format:
	@# Format code
	. $(VENV) && ruff format .

format-check:
	@# Check formatting without changing files
	. $(VENV) && ruff format --check .

pre-commit-install:
	@# Install pre-commit hooks
	. $(VENV) && pre-commit install

pre-commit-all:
	@# Run pre-commit on all files
	. $(VENV) && pre-commit run --all-files

.PHONY: bundle
