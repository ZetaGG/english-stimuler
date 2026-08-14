PORT ?= 8001

.PHONY: dev test

dev:
	uv run uvicorn app.main:app --reload --port $(PORT)

test:
	uv run pytest
