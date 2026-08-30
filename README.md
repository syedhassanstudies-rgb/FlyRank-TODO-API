# Task API

A CRUD API for managing tasks built with FastAPI and Python.
Storage has been migrated from SQLite (A2) to PostgreSQL hosted on Neon.

## How to Run

Copy the example env file and fill in your database URL:

    cp .env.example .env

Start the API:

    uv run uvicorn main:app --reload

Or with Docker Compose:

    docker compose up

Server starts at http://localhost:8000
Swagger UI at http://localhost:8000/docs

## Environment Variables

See `.env.example` for required variables:

    DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

Never commit `.env` — it is git-ignored.

## Endpoints

| Method | Path | Description | Success Code | Error Codes |
|--------|------|-------------|--------------|-------------|
| GET | / | Returns API name, version, endpoints | 200 | - |
| GET | /health | Returns API health status | 200 | - |
| GET | /tasks | Returns all tasks | 200 | - |
| GET | /tasks/{id} | Returns a single task by ID | 200 | 404 |
| POST | /tasks | Creates a new task | 201 | 400 |
| PUT | /tasks/{id} | Updates title and/or done status | 200 | 400, 404 |
| DELETE | /tasks/{id} | Deletes a task | 204 | 404 |

## Validation Rules

- POST and PUT reject empty or whitespace-only titles with 400
- All errors return JSON: {"detail": "message"}
- All queries use parameterized placeholders (%s) — no raw user input in SQL

## Database

- **Engine:** PostgreSQL hosted on Neon (cloud, free tier)
- **Why PostgreSQL over SQLite:** PostgreSQL runs as a real server, handles multiple connections, and is the same engine used in production at companies like FlyRank. SQLite is a single file — fine for local dev, not for real backends.
- **Why Neon:** Zero local install, free tier, connects via a standard PostgreSQL connection string.
- **Table is created automatically** on first run if it doesn't exist.
- **Three example tasks are seeded** only when the table is empty.

## Database Screenshot

![Database](dbrowser.png)

## Example Request

    curl -i -X POST http://localhost:8000/tasks \
      -H "Content-Type: application/json" \
      -d '{"title": "Buy milk"}'

    HTTP/1.1 201 Created
    {"id": 4, "title": "Buy milk", "done": false}

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2
- psycopg2
- PostgreSQL (Neon)
- Docker + Docker Compose
- uv