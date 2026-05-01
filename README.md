# pjsa-api

API REST com Python e FastAPI.

## Requisitos

- Python 3.11+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
cp .env.example .env
```

## Executar

Na raiz do repositório:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- `GET /health` — verificação simples
- `GET /api/v1/ping` — exemplo de rota versionada
- Com `DEBUG=true` no `.env`, `/docs` e `/redoc` ficam ativos.

## Testes

```bash
python -m pytest
```
