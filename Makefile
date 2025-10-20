.PHONY: up down logs api db

up:
\tcp .env.sample .env || true
\tdocker compose up -d --build
\tdocker compose logs -f api

down:
\tdocker compose down -v

logs:
\tdocker compose logs -f

api:
\tdocker compose exec api bash

db:
\tdocker compose exec db psql -U app -d incentives
