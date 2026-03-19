# TalkNote Backend

TalkNote backend is a Django REST API for authenticated voice-note capture and AI-assisted note enrichment.

It provides:
- Email/password authentication with JWT
- User-scoped notes CRUD
- Audio upload support
- Whisper-based transcription
- Gemini-based summary + action items extraction

## Table of Contents

- Overview
- Current Architecture
- Project Structure
- Requirements
- Quick Start (Local)
- Environment Variables
- API Documentation
- AI Processing Flow
- Security Model
- Testing
- Logging and Observability
- Deployment Checklist
- Known Constraints and Next Improvements
- Useful Commands

## Overview

The backend is implemented as a modular monolith with two feature apps:
- `users`: authentication and profile operations
- `api`: notes domain + AI services

The app enforces authenticated access to note operations and isolates each user's data through query filtering and owner-stamping during creation.

## Current Architecture

### Runtime
- Framework: Django 5.2 + Django REST Framework
- Auth: `djangorestframework-simplejwt`
- DB: SQLite (default in current settings)
- Media storage: local filesystem (`media/`)
- AI stack:
	- Transcription: `openai-whisper`
	- LLM analysis: `google-genai`

### Request Path (Audio Note)
1. Authenticated client sends `POST /api/notes/` with multipart audio.
2. API saves note and attaches current user.
3. Whisper transcribes uploaded file.
4. Gemini analyzes transcript into JSON (`summary`, `action_items`).
5. Note is updated with AI output and returned.

## Project Structure

```text
core/
	settings.py      # global config, JWT, CORS, logging
	urls.py          # root routing
users/
	models.py        # custom User model (email login + UUID PK)
	serializers.py   # register/login/profile/password serializers
	views.py         # auth endpoints
	urls.py          # /api/auth/* endpoints
api/
	models.py        # Note model
	serializers.py   # Note serializer (AI fields read-only)
	views.py         # NoteViewSet (user-scoped + AI flow)
	services.py      # Whisper + Gemini service layer
	urls.py          # /api/notes/* endpoints
```

## Requirements

- Python `>=3.10`
- `uv` package manager

Dependencies are managed in `pyproject.toml`.

## Quick Start (Local)

1) Install dependencies

```bash
uv sync
```

2) Create environment file

```bash
cp .env.example .env
```

3) Run migrations

```bash
uv run python manage.py migrate
```

4) Start server

```bash
uv run python manage.py runserver
```

5) (Optional) Create admin user

```bash
uv run python manage.py createsuperuser
```

## Environment Variables

See `.env.example`.

Minimum required values:
- `DJANGO_SECRET_KEY`
- `GEMINI_API_KEY`

Recommended additional values (future-hardening):
- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`

## API Documentation

Base URL (local): `http://localhost:8000`

### Authentication Endpoints

Prefix: `/api/auth/`

- `POST /register/`
	- Creates user and returns tokens + user profile
- `POST /login/`
	- Returns access/refresh tokens + user profile
- `POST /token/refresh/`
	- Returns new access token
- `GET /me/`
	- Returns current user profile
- `PUT /me/`
	- Updates `first_name`, `last_name`
- `POST /change-password/`
	- Requires `old_password`, `new_password`
- `POST /logout/`
	- Blacklists refresh token

### Notes Endpoints

Prefix: `/api/`

- `GET /notes/`
	- Lists notes owned by authenticated user
- `POST /notes/` (multipart supported)
	- Creates note
	- If audio provided, triggers transcription + LLM analysis
- DRF default detail endpoints also available (retrieve/update/delete)

### Authentication Header

Use Bearer token:

```http
Authorization: Bearer <access_token>
```

## AI Processing Flow

AI behavior is implemented in `api/services.py`:

- Whisper model loads at module init (`base` model).
- Transcription service:
	- Reads audio from `MEDIA_ROOT`
	- Returns transcript string or `None`
- LLM service:
	- Uses `genai.Client(api_key=GEMINI_API_KEY)`
	- Calls `gemini-3.1-flash-lite`
	- Enforces JSON output parsing
	- Retries twice with short backoff
	- Returns fallback payload on failure

Debug-aware logging is enabled:
- `DEBUG=True`: detailed exception stack traces
- `DEBUG=False`: concise error/warning logs

## Security Model

Implemented protections:
- JWT auth required by default in DRF settings
- Notes queryset restricted to current user
- Note owner assigned server-side (`serializer.save(user=request.user)`)
- AI-generated fields are read-only in serializer:
	- `transcript`
	- `summary`
	- `action_items`
- Password validation uses Django validators
- Refresh token rotation + blacklist enabled

## Testing

Run all tests:

```bash
uv run python manage.py test -v 2
```

Run by module:

```bash
uv run python manage.py test users -v 2
uv run python manage.py test api -v 2
```

Current test coverage includes:
- Registration, login, profile, password change, logout
- Note creation with/without audio
- Failure resilience for transcription and LLM paths
- User-scoped notes listing

## Logging and Observability

Configured in `core/settings.py`:
- Console handler
- File handler at `logs/talknote.log`
- App-specific loggers for `users` and `api`

`logs/` is ignored by git.

## Deployment Checklist

Before production deployment:

1. Set `DEBUG=False`
2. Set secure `DJANGO_SECRET_KEY`
3. Set `ALLOWED_HOSTS`
4. Move from SQLite to PostgreSQL
5. Configure static/media serving (CDN/object storage or Nginx)
6. Run behind reverse proxy
7. Use production WSGI/ASGI server
8. Add HTTPS and security headers at edge
9. Add request throttling/rate limits
10. Add monitoring/alerting

## Known Constraints and Next Improvements

Current known constraints:
- `DEBUG` is hardcoded `True` in settings (should be env-driven).
- `ALLOWED_HOSTS` is hardcoded empty.
- `CORS_ALLOWED_ORIGINS` is hardcoded list.
- Note `user` field in model is nullable for compatibility, while app logic always sets owner.
- Whisper loads on process start (can increase startup latency).

Recommended next iteration:
- Make `DEBUG`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` fully env-driven.
- Offload AI work to background queue (Celery/RQ) for scalability.
- Add throttling and stricter upload validation.
- Add CI pipeline (lint + tests).

## Useful Commands

```bash
# Health check
uv run python manage.py check

# Run app
uv run python manage.py runserver

# Run tests
uv run python manage.py test -v 2

# Migrations
uv run python manage.py makemigrations
uv run python manage.py migrate
```

