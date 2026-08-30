# Task API — with Authentication

A CRUD API for managing tasks with full user authentication, built with FastAPI and Python.
Uses Supabase Auth as the Identity Provider — no passwords are stored or hashed by this server.

## Setup

Copy the example env file and fill in your values:

    cp .env.example .env

Your .env needs these values:

    DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
    SUPABASE_URL=https://your-project-ref.supabase.co
    SUPABASE_KEY=your_supabase_anon_key

Never commit .env — it is git-ignored. See .env.example for the key names.

## How to Run

    uv run uvicorn main:app --reload

Server starts at http://localhost:8000
Swagger UI at http://localhost:8000/docs

## Endpoints

| Method | Path | Description | Auth Required | Success Code |
|--------|------|-------------|---------------|--------------|
| GET | / | API info | No | 200 |
| GET | /health | Health check | No | 200 |
| GET | /public/info | Public endpoint | No | 200 |
| POST | /auth/signup | Register new user | No | 201 |
| POST | /auth/login | Login and get JWT | No | 200 |
| POST | /auth/logout | Logout current user | Yes — Bearer token | 204 |
| GET | /protected/profile | Get current user profile | Yes — Bearer token | 200 |
| GET | /protected/dashboard | Protected dashboard | Yes — Bearer token | 200 |
| GET | /tasks | Get all tasks | No | 200 |
| GET | /tasks/{id} | Get task by ID | No | 200 / 404 |
| POST | /tasks | Create a task | No | 201 / 400 |
| PUT | /tasks/{id} | Update a task | No | 200 / 400 / 404 |
| DELETE | /tasks/{id} | Delete a task | No | 204 / 404 |

## Authentication Flow

    1. POST /auth/signup  → create account
    2. POST /auth/login   → get access_token
    3. Use token in header: Authorization: Bearer <access_token>
    4. POST /auth/logout  → end session

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request — missing or invalid input |
| 401 | Unauthorized — missing, invalid, or expired token |
| 404 | Not Found — resource does not exist |

## Validation Rules

- Signup and login reject missing email or password with 400
- POST and PUT on tasks reject empty or whitespace-only titles with 400
- All errors return JSON: {"detail": "message"}
- All SQL queries use parameterized placeholders — no raw user input in SQL

## How Auth Works

    Client → POST /auth/login → Supabase returns JWT
    Client → GET /protected/profile with Authorization: Bearer <token>
    Server → supabase.auth.get_user(token) → verified or 401

Your server never stores passwords. Supabase handles accounts, hashing, and token signing.
Your server only verifies tokens using the Supabase SDK.

## Swagger UI

The lock icon appears on protected routes. Click Authorize, paste your access_token, and
all protected endpoints work from the browser without curl.

![Swagger UI](swagger.PNG)

## Database

- PostgreSQL hosted on Neon (cloud, free tier)
- Table created automatically on first run
- Three example tasks seeded only when table is empty

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic v2
- psycopg2
- Supabase Auth
- PostgreSQL (Neon)
- uv