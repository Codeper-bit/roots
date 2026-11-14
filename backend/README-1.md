# Roots backend

Oral-history preservation platform. *AI helps preserve the story. The storyteller decides what is true.*

**Status: Day 1.** Database schema, configuration, and connection pooling only. There are no API
routes yet. Authentication, story endpoints, audio upload and AI processing come later.

Stack: Python 3.11+, FastAPI, PostgreSQL 13+, asyncpg (raw SQL, no ORM), Pydantic, pytest.

## Layout

```
app/
  main.py            FastAPI app + lifespan (opens/closes the DB pool)
  core/config.py     environment-based settings
  core/database.py   asyncpg pool + acquire()/transaction() helpers
  api/routes/        HTTP endpoints (empty for now)
  api/schemas/       Pydantic request/response models (empty for now)
  services/          business logic (empty for now)
  repositories/      SQL queries (empty for now)
  models/            dataclasses for DB rows (empty for now)
  workers/           future background processing (empty for now)
sql/001_initial.sql  the full schema
tests/               real-PostgreSQL tests
docs/PERMANENT_ERASURE.md  design note for eventual permanent erasure (not implemented)
```

## 1. Run PostgreSQL locally

Option A, Docker (simplest). The password below is for local development only:

```bash
docker run --name roots-postgres -d -p 5432:5432 \
  -e POSTGRES_USER=roots -e POSTGRES_PASSWORD=change-me -e POSTGRES_DB=roots \
  postgres:16
docker exec roots-postgres createdb -U roots roots_test
```

Option B, a native install (Ubuntu example):

```bash
sudo apt install postgresql
sudo -u postgres psql -c "CREATE USER roots WITH PASSWORD 'change-me';"
sudo -u postgres createdb -O roots roots
sudo -u postgres createdb -O roots roots_test
```

## 2. Configure the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # then edit DATABASE_URL if your credentials differ
```

`.env` is git-ignored. Never commit it.

## 3. Create the schema (development database)

```bash
psql "postgresql://roots:change-me@localhost:5432/roots" -v ON_ERROR_STOP=1 -f sql/001_initial.sql
```

The file runs inside one transaction: it fully applies or not at all. It is **not** idempotent
(re-running it on an already-migrated database fails). A migration tool is a later decision.

## 4. Run the tests

The tests **drop and recreate the `public` schema** of the database in `TEST_DATABASE_URL`, then
apply `sql/001_initial.sql`. They refuse to run unless the database name ends in `_test`.

```bash
export TEST_DATABASE_URL="postgresql://roots:change-me@localhost:5432/roots_test"
pytest -v
```

## Development scaffolding warning

The endpoints planned for Day 2 (`POST /users`, `GET /stories`, ...) will have **no authentication**.
They are development scaffolding. Do not deploy them to production: they would expose private
user and story data to anyone.
