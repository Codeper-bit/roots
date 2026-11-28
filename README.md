# Roots

**Preserve the story. Keep the storyteller in charge.**

Roots is an intergenerational storytelling and memory-preservation platform. A family member records an older relative telling a story, Roots stores the original audio privately, and AI produces a written transcript and, optionally, a translation. Every piece of AI output is a draft: it stays labelled as such until a person reviews it, and the original recording is never replaced.

> AI helps preserve the story. The storyteller decides what is true.

The first languages the project targets are Yoruba, Hausa and Igbo (plus English as a translation target), but nothing in the data model is specific to them: a language is a row in a lookup table.

![React](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-61DAFB?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/auth%20%26%20storage-Supabase-3FCF8E?logo=supabase&logoColor=white)
![Groq](https://img.shields.io/badge/AI-Groq-F55036)

---

## Table of contents

- [The problem](#the-problem)
- [What Roots does](#what-roots-does)
- [Core engineering principles](#core-engineering-principles)
- [System architecture](#system-architecture)
- [Technology stack](#technology-stack)
- [Database design](#database-design)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [API overview](#api-overview)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security and privacy](#security-and-privacy)
- [Current limitations and roadmap](#current-limitations-and-roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## The problem

First-hand family history lives in the memory of the people who lived it, and it is lost when they are no longer able to tell it. Recording audio is a good first step, but it does not solve the problem on its own.

- **Audio is hard to use.** A recording cannot be skimmed, searched or quoted, and few people will listen to an hour of audio to find one story.
- **Language gets in the way.** In many families the oldest generation speaks a language that younger relatives, often living in another country, read or understand only partly. A faithful recording that no one can follow is still inaccessible.
- **Context disappears.** Without who told the story, who was present, when it was recorded and what was agreed about its use, a recording loses much of its meaning and its owner's authority over it.
- **Machine output is not testimony.** Automatic transcription and translation make mistakes, and those mistakes are worse for lower-resource languages. If a generated text silently replaces the original account, the storyteller's voice is lost.

Roots treats the original recording as the source of truth, treats everything derived from it as a suggestion, and keeps the link between the two.

## What Roots does

### Implemented

The following is wired end to end between the React frontend and the FastAPI backend.

| Step | What happens |
| --- | --- |
| **Sign up and sign in** | Email and password through Supabase Auth. The backend verifies the access token with Supabase on every request and links it to a Roots profile. |
| **Create a story** | Title, description, source language and visibility (`private` or `family`). Stories are soft-deleted. |
| **Add participants** | Storyteller, interviewer, family member, translator, reviewer or other. Participants do not need an account. |
| **Manage consent** | Per participant and per purpose: `audio_storage`, `transcription`, `translation`, `cultural_interpretation`, `family_sharing`. Grants can be withdrawn and the history is kept. |
| **Record or upload audio** | Record in the browser (MediaRecorder) or upload a file. The server stores it in a private Supabase Storage bucket and records its size and SHA-256 checksum. |
| **Transcribe** | `POST /transcriptions` sends the stored audio to Groq (Whisper) and saves the result as a new `ai_generated` transcript version. |
| **Translate** | `POST /translations` asks a Groq chat model to translate an existing transcript into English, Yoruba, Hausa or Igbo. The result is saved as an `ai_generated` translation. A person can also write or correct a translation by hand. |
| **Review** | A person approves, rejects or requests changes on any version. Corrections are saved as new `human_edited` versions that point at the version they correct. |
| **Follow-up questions** | A story can hold questions to ask the storyteller next time. They are entered by hand. |
| **Share** | For stories that are not private, a Share dialog sends approved text through WhatsApp, e-mail, the device share sheet or the clipboard. See [Sharing](#sharing). |
| **Processing history** | Each transcription and translation attempt is recorded as a processing job with its status and a user-safe error message. |

### Not implemented

These appear in the schema or the type definitions, but no feature uses them yet:

- Automatic generation of cultural interpretations (the `interpretation` content type and the `cultural_interpretation` consent exist; nothing produces interpretation text).
- Automatic generation of follow-up questions (`question_generation` is an allowed job type; nothing runs it).
- Playback of stored audio after a page reload. See [limitations](#current-limitations-and-roadmap).

### Sharing

Sharing is deliberately limited and happens in the browser, not on the server:

- The button appears only when the story's visibility is not `private`.
- The storyteller must have granted the `family_sharing` consent.
- Only the latest **approved** transcript or translation is offered. Unreviewed AI drafts and audio are never shared.
- What leaves the app is plain text, so the recipient does not need a Roots account. There is no public link and no public story feed; the database does not allow a `public` visibility.

The `family_sharing` check is made by the frontend. The backend does not see the share action.

## Core engineering principles

| Principle | How it is implemented |
| --- | --- |
| **Preserve the original source** | Audio bytes go to object storage under `stories/{story_id}/audio/{uuid}`. A database trigger (`protect_audio_assets`) blocks changing an audio asset's location, and freezes its status, size and checksum once the upload is complete. Uploads use `upsert: false`, so an existing object is never overwritten. |
| **Humans control AI output** | AI results are stored with `origin = 'ai_generated'` and `review_status = 'unreviewed'`. A database trigger (`guard_content_versions`) refuses to set `review_status = 'approved'` unless the most recent review is an approval. The share feature offers only approved text. |
| **Never edit, always version** | `content_versions` is append-only in effect: the same trigger rejects any change to text, language, origin or lineage. A correction is a new row with `based_on_version_id`; a composite foreign key guarantees it belongs to the same story. |
| **Explicit consent** | Services call `require_active_consent` before storing audio, transcribing and translating. The database allows at most one active grant per participant and purpose, and withdrawal keeps the row and its timestamps. |
| **Separate bytes from records** | Audio lives in Supabase Storage. PostgreSQL holds only metadata (`audio_assets`): key, MIME type, size, duration, checksum, upload status. |
| **Modular backend** | Routers handle HTTP, services hold business rules, repositories hold SQL. Provider and database failures are converted into user-safe errors in one place (`app/api/error_handlers.py`). |
| **Privacy and access control** | Every route except `/health` needs a verified Supabase token. Records are reached through the story, and a story is visible only to its owner. Non-owners get `404`, so identifiers cannot be probed. Nothing cascades on delete: all foreign keys are `ON DELETE RESTRICT`. |

## System architecture

```mermaid
flowchart LR
    User([Family member])

    subgraph Browser["Browser"]
        FE["React + TypeScript SPA"]
    end

    subgraph API["FastAPI backend"]
        MW["Middleware: CORS, error handling"]
        RT["Routers"]
        AZ["Auth and ownership checks"]
        SV["Services"]
        RP["Repositories"]
        MW --> RT --> AZ --> SV --> RP
    end

    subgraph Supabase["Supabase"]
        AUTH["Supabase Auth"]
        PG[("PostgreSQL")]
        ST[("Storage: private audio bucket")]
    end

    GROQ["Groq API: Whisper and chat model"]

    User --> FE
    FE -- "sign in / sign up (anon key)" --> AUTH
    FE -- "REST + Bearer token" --> MW
    AZ -- "verify token" --> AUTH
    RP -- "SQL via asyncpg" --> PG
    SV -- "upload / download (service role)" --> ST
    SV -- "transcribe / translate" --> GROQ
```

**Frontend.** A single-page React app. It talks to Supabase Auth directly for sign-in with the public anon key, and to the Roots API for everything else, attaching the access token to each request. It has a small History-API router instead of a routing library.

**Middleware.** CORS, plus an error layer that turns every failure into JSON. This matters in the browser: an unhandled server error normally bypasses CORS headers, and the browser then reports a generic network failure instead of the real problem.

**Routers.** Thin HTTP handlers in `backend/app/api/routes/`. They validate input with Pydantic schemas and call services.

**Authorization.** `auth_dependencies.py` verifies the bearer token with Supabase Auth and resolves it to a row in `users`. `authorization.py` resolves any record (participant, consent, audio asset, content version, job, question) to its story and checks that the caller owns it.

**Services.** Business rules: consent checks, upload orchestration with cleanup, transcription and translation jobs, review handling. The Groq engines are created at startup and injected through application state.

**Repositories.** All SQL, written directly with `asyncpg` (there is no ORM).

**Supabase.** PostgreSQL holds relational data, Storage holds audio, Auth manages passwords and sessions. The backend uses the service-role key for Storage and for token verification; that key never reaches the browser.

**Groq.** `whisper-large-v3-turbo` by default for transcription, and a configurable chat model for translation.

## Technology stack

| Category | Technology | Why |
| --- | --- | --- |
| **Frontend** | React, TypeScript | Component model and static typing across API types. |
| | Vite-style build (`import.meta.env`) | Environment variables are read through `VITE_`-prefixed names. |
| | Custom History-API router (`src/lib/router.tsx`) | About a dozen routes; avoids an extra dependency. |
| | Browser MediaRecorder API | In-browser recording without a plugin. |
| **Backend** | Python, FastAPI | Async handlers, dependency injection, automatic request validation and OpenAPI docs. |
| | Pydantic, pydantic-settings | Typed schemas and typed, validated configuration. |
| | asyncpg | Direct, fast PostgreSQL access with explicit SQL. |
| **Database** | PostgreSQL 13+ | Constraints, partial unique indexes and triggers enforce the data rules. |
| **Object storage** | Supabase Storage | Private bucket for original recordings. |
| **Authentication** | Supabase Auth | Email and password handled by a managed service; Roots stores no passwords for new accounts. |
| **AI** | Groq (Whisper for speech-to-text, a chat model for translation) | Hosted inference behind one API key. |
| **Testing** | pytest, anyio, FastAPI TestClient | Unit tests with the database and providers stubbed. |

## Database design

The schema is in [`backend/sql/`](backend/sql/) and is applied with `psql`. Foreign keys are all `ON DELETE RESTRICT`, stories are soft-deleted, and several tables are protected by triggers.

```mermaid
erDiagram
    users ||--o{ stories : owns
    languages ||--o{ stories : "source_language"
    stories ||--o{ story_participants : has
    users |o--o{ story_participants : "optional account"
    story_participants ||--o{ consent_records : grants
    stories ||--o{ audio_assets : contains
    stories ||--o{ content_versions : contains
    languages ||--o{ content_versions : "language_code"
    users |o--o{ content_versions : created_by
    content_versions |o--o{ content_versions : based_on
    content_versions ||--o{ content_reviews : reviewed_by
    users ||--o{ content_reviews : writes
    stories ||--o{ processing_jobs : tracks
    audio_assets |o--o{ processing_jobs : "audio_asset_id"
    stories ||--o{ story_questions : has
```

| Table | Purpose and notable rules |
| --- | --- |
| `languages` | Lookup keyed by 2 or 3 letter code. Seeded with `yo`, `ha`, `ig`; `en` is added by migration 003. Adding a language is an `INSERT`. |
| `users` | Application profile. `supabase_auth_id` (migration 002) links to Supabase Auth; `password_hash` is nullable and only used by pre-Supabase legacy rows. Emails must be lower-case. |
| `stories` | Belongs to one owner. `status` is `draft`, `processing`, `in_review` or `completed`. `visibility` is `private` or `family`. `deleted_at` marks a soft delete. |
| `story_participants` | A person in a story, with a role. `user_id` is optional. |
| `consent_records` | One row per decision. Partial unique index `consent_records_one_active_grant` allows one active grant per participant and purpose. A `CHECK` ties `granted_at` and `withdrawn_at` to the status. |
| `audio_assets` | Metadata only. Unique `storage_key`; bare `audio/*` MIME type; a completed upload must have size and a SHA-256 checksum. Immutable once `uploaded`. |
| `content_versions` | Transcripts, translations and interpretations. Unique on `(story_id, content_type, language_code, version_number)`. `origin` is `ai_generated`, `human_created` or `human_edited`; human origins require `created_by`; an edit requires `based_on_version_id`. |
| `content_reviews` | Append-only review decisions (`approved`, `rejected`, `changes_requested`). |
| `processing_jobs` | Transcription and translation attempts with `status`, `attempts` and `error_message`. A composite foreign key ties a job's audio to the same story. `completed_at` is set exactly when the status is final. |
| `story_questions` | Follow-up questions with status `suggested`, `asked` or `dismissed`. |

Content version numbers are allocated inside a transaction guarded by a PostgreSQL advisory lock, so two simultaneous saves get consecutive numbers instead of failing on the unique constraint.

## Project structure

```text
.
├── README.md
├── backend/
│   ├── pytest.ini
│   ├── sql/                       # 001 initial schema, 002 Supabase Auth, 003 English
│   ├── tests/                     # pytest suite (no database required)
│   └── app/
│       ├── main.py                # app factory, lifespan, middleware, router registration
│       ├── core/                  # settings, DB pool, storage client, error types
│       ├── api/
│       │   ├── routes/            # one router per domain
│       │   ├── auth_dependencies.py   # token verification, current profile
│       │   ├── authorization.py       # story-ownership checks
│       │   ├── error_handlers.py      # JSON errors that keep CORS headers
│       │   └── dependencies.py        # DB connection, storage client
│       ├── schemas/               # Pydantic request and response models
│       ├── services/              # business rules, Groq engines, storage
│       └── repositories/          # SQL (asyncpg)
└── src/                           # React frontend
    ├── main.tsx, App.tsx
    ├── api/                       # typed REST client and per-domain calls
    ├── auth/                      # Supabase session context
    ├── components/                # dashboard, layout, recording, review, story, transcription, ui
    ├── hooks/                     # data loading, consents, audio recording
    ├── lib/                       # router, Supabase client, workflow state, consent, sharing
    ├── pages/                     # one component per route
    ├── styles/globals.css
    ├── types/index.ts             # shared API types
    └── utils/
```

`src/counter.js`, `src/main.js`, `src/style.css` and the SVGs in `src/assets/` appear to be unused leftovers from the Vite template.

## Getting started

### Prerequisites

- Node.js and npm
- Python 3.10 or newer (the code uses `X | None` union types and `asyncio.to_thread`)
- A PostgreSQL 13+ database. Supabase provides one.
- A Supabase project with Auth enabled (email and password) and a **private** Storage bucket
- A Groq API key for transcription and translation

### 1. Clone

```bash
git clone <your-repository-url> roots
cd roots
```

### 2. Database

Apply the migrations in order against an empty database:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/sql/001_initial.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/sql/002_supabase_auth.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/sql/003_add_english.sql
```

In the Supabase dashboard, create a Storage bucket whose name matches `SUPABASE_STORAGE_BUCKET` (default `roots-audio`) and keep it private.

### 3. Backend

PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" asyncpg pydantic-settings supabase groq python-multipart
pip install pytest anyio httpx   # for tests
```

macOS and Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" asyncpg pydantic-settings supabase groq python-multipart
pip install pytest anyio httpx   # for tests
```

Create `backend/.env` (see [Environment variables](#environment-variables)), then run the API **from the `backend` directory**, because settings read `.env` from the working directory:

```bash
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`. Interactive docs are served by FastAPI at `/docs`.

### 4. Frontend

From the repository root, create a `.env` file with the three `VITE_` variables, then:

```bash
npm install
npm run dev
```

The Vite dev server uses port 5173 by default, which is already in the backend's default CORS origins.

### 5. First run

1. Open the app and register. Confirm the email address (the backend refuses to create a profile for an unconfirmed email).
2. Create a story, add the storyteller, and record consent.
3. Record or upload audio, then transcribe it.

## Environment variables

### Backend (`backend/.env`)

These are read by `app/core/config.py`. Never commit this file.

| Variable | Purpose | Required |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string. Must start with `postgresql://` or `postgres://`. | Yes |
| `SUPABASE_URL` | Supabase project URL (`http` or `https`). | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Service-role key used for Storage and for verifying user tokens. | Yes |
| `SUPABASE_STORAGE_BUCKET` | Name of the private audio bucket. Default `roots-audio`. | No |
| `GROQ_API_KEY` | Key for transcription, and for translation unless a separate key is set. Without it, both features are disabled and the API returns `503`. | No |
| `GROQ_TRANSCRIPTION_MODEL` | Speech-to-text model. Default `whisper-large-v3-turbo`. | No |
| `GROQ_TRANSLATION_MODEL` | Chat model used for translation. Default `openai/gpt-oss-120b`. Check that the model is available to your Groq account. | No |
| `GROQ_TRANSLATION_API_KEY` | Separate key for translation. Falls back to `GROQ_API_KEY`. | No |
| `CORS_ORIGINS` | Allowed browser origins, as a JSON list, for example `["https://app.example.com"]`. Default is the local Vite origins. | No |
| `ENVIRONMENT` | `development`, `test` or `production`. Default `development`. | No |
| `DB_POOL_MIN_SIZE` | Minimum connections in the pool. Default `2`. | No |
| `DB_POOL_MAX_SIZE` | Maximum connections in the pool. Default `10`. Must not be below the minimum. | No |
| `DB_COMMAND_TIMEOUT` | Database command timeout in seconds. Default `30`. | No |

Example with placeholders:

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=roots-audio
GROQ_API_KEY=your-groq-api-key
GROQ_TRANSCRIPTION_MODEL=whisper-large-v3-turbo
GROQ_TRANSLATION_MODEL=openai/gpt-oss-120b
CORS_ORIGINS=["http://localhost:5173"]
```

### Frontend (`.env` in the project root)

Vite exposes `VITE_` variables to the browser, so only public values belong here.

| Variable | Purpose | Required |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Base URL of the Roots API. Defaults to `http://127.0.0.1:8000`. | No (yes in production) |
| `VITE_SUPABASE_URL` | Supabase project URL. | Yes |
| `VITE_SUPABASE_ANON_KEY` | Supabase **anon** (public) key. | Yes |

> **Warning.** Never put `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL` or any Groq key in frontend code or in a `VITE_` variable. The service-role key bypasses Supabase's access rules. If one of these keys has been exposed, rotate it.

## API overview

Every endpoint except `GET /health` requires an `Authorization: Bearer <Supabase access token>` header. Unless noted, a record is reachable only by the owner of its story, and anything else returns `404`.

Errors are JSON of the form `{"detail": "..."}`.

### Health and authentication

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | API and database liveness. Public. |
| GET | `/auth/me` | Identity of the verified token. |
| POST | `/auth/profile` | Create the Roots profile for the signed-in user. Requires a confirmed email. |

### Stories

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/stories` | Create a story owned by the caller. |
| GET | `/stories` | List the caller's stories. |
| GET | `/stories/{story_id}` | Get one story. |
| DELETE | `/stories/{story_id}` | Soft-delete a story. |

The legacy `owner_id` field and query parameter are still accepted, but must equal the caller's id (`403` otherwise).

### Participants and consent

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/participants` | Add a participant to a story. |
| GET | `/participants/{participant_id}` | Get a participant. |
| GET | `/stories/{story_id}/participants` | List a story's participants. |
| PATCH | `/stories/{story_id}/participants/{participant_id}` | Update name or role. |
| POST | `/consents` | Record a grant or decline for a purpose. |
| GET | `/consents/{consent_id}` | Get a consent record. |
| GET | `/participants/{participant_id}/consents` | Full consent history. |
| GET | `/participants/{participant_id}/consents/{purpose}/active` | Active grant for a purpose, or `404`. |
| POST | `/consents/{consent_id}/withdraw` | Withdraw an active grant. |

### Audio

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/audio-assets/upload` | Multipart upload (50 MB limit). Needs `audio_storage` consent. Stores the file and its checksum. |
| POST | `/audio-assets` | Register metadata for an object already in storage. The key must be inside the story's `stories/{story_id}/audio/` prefix. |
| GET | `/audio-assets/{audio_asset_id}` | Get audio metadata. There is no endpoint that returns the audio itself. |
| POST | `/audio-assets/{audio_asset_id}/complete` | Mark a registered upload as complete. |
| POST | `/audio-assets/{audio_asset_id}/fail` | Mark a pending upload as failed. |

### Transcription, translation and content

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/transcriptions` | Transcribe an uploaded asset with Groq. Synchronous. Needs `transcription` consent. |
| POST | `/translations` | Translate a transcript to `en`, `yo`, `ha` or `ig`. Synchronous. Needs `translation` consent. |
| POST | `/content-versions` | Save a human-written or human-edited version. |
| GET | `/content-versions/{content_version_id}` | Get one version. |
| GET | `/stories/{story_id}/content-versions` | All versions of a story. |
| GET | `/stories/{story_id}/content/latest` | Latest version for `content_type` and `language_code` (query parameters). |
| POST | `/content-reviews` | Approve, reject or request changes on a version. |
| GET | `/content-reviews/version/{content_version_id}` | Review history of a version. |
| GET | `/content-reviews/reviewer/{reviewer_id}` | The caller's own review history only. |

### Processing jobs and questions

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/processing-jobs` | Create a job record. |
| GET | `/processing-jobs/story/{story_id}` | Jobs for a story, newest first. |
| GET | `/processing-jobs/{processing_job_id}` | Get one job. |
| PATCH | `/processing-jobs/{processing_job_id}/status` | Set a job's status. |
| POST | `/story-questions` | Add a follow-up question. |
| GET | `/story-questions/{question_id}` | Get one question. |
| GET | `/stories/{story_id}/questions` | List a story's questions. |
| PATCH | `/story-questions/{question_id}/status` | Mark a question `suggested`, `asked` or `dismissed`. |

## Testing

```bash
cd backend
pytest
```

`pytest.ini` sets `testpaths = tests`. The suite needs no database, Supabase project or Groq key: route tests replace the database connection and the authenticated profile with test doubles, and the Groq engine tests mock the Groq client.

| File | What it covers |
| --- | --- |
| `tests/test_stories.py` | Story routes: ownership comes from the token, another user's `owner_id` is rejected with `403`, not-found handling, validation. |
| `tests/test_groq_transcription.py` | Language hint handling (Igbo is sent without one), MIME normalization, size limits, and mapping of Groq failures to user-safe errors without leaking provider text. |
| `tests/test_speech_languages.py` | Which languages are sent to Whisper as an explicit hint. |
| `tests/test_authorization.py` | The `ensure_self` identity check. |

Not covered: the SQL itself and the database triggers (there are no database integration tests), the frontend (no frontend tests exist), and the upload and review flows end to end. Test counts are not listed here because they change as tests are added.

## Deployment

The repository contains no deployment configuration files (no Dockerfile, `render.yaml` or `vercel.json`), so the following describes what the code requires rather than a prescribed setup.

| Component | Responsibility | What it needs |
| --- | --- | --- |
| **Frontend host** (any static host) | Serves the built single-page app. | `VITE_API_BASE_URL`, `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` set at **build** time. A rewrite so that deep links such as `/stories/...` serve `index.html`, because routing is client-side. |
| **Backend host** (any ASGI host) | Runs the FastAPI app. | The backend variables above. Start command, from `backend/`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. `CORS_ORIGINS` must include the frontend's exact origin. |
| **Supabase** | PostgreSQL, Auth and private Storage. | Migrations applied; a private bucket matching `SUPABASE_STORAGE_BUCKET`; email confirmation settings and redirect URLs configured for the frontend's address. |
| **Groq** | Speech-to-text and translation. | An API key, and access to the configured models. |

Keep the service-role key and the database URL as secret environment variables on the backend host only. After changing any variable, restart or redeploy the backend.

No live or demo URL is listed because none is recorded in the repository.

## Security and privacy

What the code does:

- **Authentication.** Supabase Auth manages credentials. The backend validates each bearer token by asking Supabase (`auth.get_user`), not by trusting decoded claims, and maps it to a profile. Profile creation requires a confirmed email.
- **Authorization.** Every record is resolved to its story and must belong to the caller. Identity comes from the token. Client-supplied `owner_id`, `created_by` and `reviewer_id` are accepted only if they match the caller. Responses use `404` for both missing and foreign records.
- **Consent.** Audio storage, transcription and translation each check for an active grant before running. Consent history is preserved.
- **Private audio.** Audio is stored in a private bucket under an unguessable key, and the API exposes no endpoint that returns it. A registered storage key must sit inside the story's own prefix, so one story cannot claim another's object.
- **Database.** Constraints and triggers protect original audio, version history and review integrity. No foreign key cascades.
- **Credentials and errors.** Secrets are `SecretStr` settings and are never returned. Provider and database errors are mapped to short messages; raw provider output is not shown or stored in job records.

What it does not do, so that nothing is assumed:

- **Story-owner model only.** Access is granted to the story's owner. There are no per-participant permissions, and a storyteller without an account cannot sign in to approve their own story. Approval is done by the signed-in owner on the storyteller's behalf.
- **Reviewer authorization is not role-based.** The database proves that an approving review exists, not that the reviewer is the storyteller or a designated reviewer.
- **Consent is not retroactive.** Withdrawing a consent blocks future processing. It does not delete existing audio, transcripts or translations.
- **`family_sharing` is enforced in the UI only.** Text that has been shared by WhatsApp, e-mail or copy is outside Roots' control.
- **Third-party processing.** Audio and transcript text are sent to Groq for transcription and translation. Review Groq's terms before using real family recordings.
- **No rate limiting, audit log or permanent-erasure process.** The SQL header refers to a `docs/PERMANENT_ERASURE.md` that is not in the repository; erasure is not implemented.
- **Service-role key.** The backend holds a key that bypasses Supabase's row-level rules, so a backend compromise exposes the whole bucket. Storage access control relies on the API.

## Current limitations and roadmap

### Implemented

Everything in [What Roots does](#what-roots-does) under "Implemented".

### Known limitations

- **No audio download.** `storage_service.generate_download_url` exists, but no route exposes it. In the UI a recording can be played only in the browser tab where it was recorded or uploaded, and only until the page reloads.
- **Igbo transcription is a best effort.** Whisper does not support Igbo and rejects an explicit `ig` language hint. Roots sends the audio without a hint and the model guesses the language, so output will often be wrong. The UI warns about this. Yoruba and Hausa are supported by Whisper, but quality varies for both. Check transcripts before translating them.
- **Translation quality is unverified** for Yoruba, Hausa and Igbo. Translations are always saved as unreviewed AI drafts.
- **Synchronous AI calls.** Transcription and translation run inside the HTTP request, with a 25 MB limit imposed by Groq, a 50 MB upload limit in the API, and no background worker or queue.
- **Fixed translation targets.** The API accepts only `en`, `yo`, `ha` and `ig`. Other language codes can be added by hand but not machine-translated.
- **Job status endpoint is permissive.** `PATCH /processing-jobs/{id}/status` lets the story owner set any valid status.
- **Test coverage is partial.** See [Testing](#testing).

### Planned

These are directions, not commitments, and none is implemented today:

- Secure audio playback through short-lived signed URLs.
- Storyteller-confirmed contextual explanations of words, places and customs.
- Broader language support and better speech recognition for the languages Whisper handles poorly.
- Shared family archives with per-person roles, so the storyteller can review without the owner acting for them.
- Search across transcripts and translations.
- Background processing for long recordings.
- Stronger privacy controls, including a permanent-erasure process and an audit trail.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/short-description`.
3. Make your changes. Keep SQL in repositories, business rules in services and HTTP concerns in routers.
4. Run the tests with `pytest` from `backend/`, and run the frontend build to check types.
5. Open a pull request describing the change and how you verified it.

Schema changes go in a new numbered file in `backend/sql/`; do not edit migrations that have already been applied.

## License

No license has been specified for this project. Until one is added, all rights are reserved by the authors.
