# 📘 TalkNote API Documentation

**Base URL:** `http://127.0.0.1:8000/api`  
**Current Version:** `v1` (URL path is not version-prefixed yet)  
**Authentication:** JWT Bearer token required for all API endpoints except register/login/token refresh

---

## 0. Authentication First (Required)

Before calling notes endpoints, obtain an access token.

### Register
- **Endpoint:** `/auth/register/`
- **Method:** `POST`
- **Content-Type:** `application/json`

```json
{
	"email": "user@example.com",
	"password": "StrongPass123!",
	"password_confirm": "StrongPass123!",
	"first_name": "Amal",
	"last_name": "K"
}
```

### Login
- **Endpoint:** `/auth/login/`
- **Method:** `POST`

```json
{
	"email": "user@example.com",
	"password": "StrongPass123!"
}
```

### Use access token

```http
Authorization: Bearer <access_token>
```

---

## 1. Create & Upload Voice Note

Primary endpoint for uploading audio. If `audio_file` is included, backend automatically attempts transcription + AI analysis.

- **Endpoint:** `/notes/`
- **Method:** `POST`
- **Auth:** ✅ Required
- **Content-Type:** `multipart/form-data`

> **Important:** Use `FormData` for file upload. Do not send raw JSON for audio uploads.

### Request Body (FormData)

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `audio_file` | File | ❌ No | Audio file (`.mp3`, `.wav`, `.webm`, `.m4a`). |
| `title` | String | ❌ No | User-defined title. Defaults to `New Voice Note`. |

### Response (201 Created)

```json
{
	"id": "b4e0afad-0330-4522-a5c6-67bd7fafd839",
	"title": "Project Brainstorming",
	"audio_file": "http://127.0.0.1:8000/media/voice_notes/recording.mp3",
	"transcript": "Okay, so for the new feature we need to...",
	"summary": "Team discussed the new feature scope.",
	"action_items": ["Draft API contract", "Schedule follow-up"],
	"created_at": "2026-03-19T11:30:00Z"
}
```

If AI fails (rate limit, model issues, etc.), note creation still succeeds and fields may remain empty.

---

## 2. List All Notes (Current User Only)

Fetches the authenticated user's notes only, sorted by newest first.

- **Endpoint:** `/notes/`
- **Method:** `GET`
- **Auth:** ✅ Required

### Response (200 OK)

```json
[
	{
		"id": "b4e0afad-0330-4522-a5c6-67bd7fafd839",
		"title": "Project Brainstorming",
		"audio_file": "http://127.0.0.1:8000/media/voice_notes/recording.mp3",
		"transcript": "Okay, so for the new feature...",
		"summary": "Team discussed feature scope.",
		"action_items": ["Send recap"],
		"created_at": "2026-03-19T11:30:00Z"
	}
]
```

---

## 3. Get / Update / Delete a Note

Manage one note by UUID.

- **Endpoint:** `/notes/<id>/`
	- Example: `/notes/b4e0afad-0330-4522-a5c6-67bd7fafd839/`
- **Auth:** ✅ Required

### Supported Methods

| Method | Description | Payload Example |
| :--- | :--- | :--- |
| `GET` | Retrieve full details for one note. | N/A |
| `PUT` / `PATCH` | Update note fields (`title`, `audio_file`). | `{ "title": "Updated Title" }` |
| `DELETE` | Permanently remove the note record. | N/A |

> **Security note:** `transcript`, `summary`, and `action_items` are read-only from API input and are managed by backend AI flow.

---

## 4. User Profile & Session Endpoints

All below are under `/api/auth/`.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/me/` | `GET` | Get current profile |
| `/me/` | `PUT` | Update `first_name`, `last_name` |
| `/change-password/` | `POST` | Change password using old+new password |
| `/logout/` | `POST` | Blacklist refresh token |
| `/token/refresh/` | `POST` | Refresh access token |

---

## 💾 Data Model Reference (Note)

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID (String) | Unique identifier |
| `title` | String | Max 200 chars |
| `audio_file` | URL (String or null) | Uploaded audio path |
| `transcript` | String or null | Whisper-generated text |
| `summary` | String or null | Gemini-generated summary |
| `action_items` | Array | Gemini-generated tasks |
| `created_at` | DateTime (ISO) | Creation timestamp |

---

## ⚛️ React Integration Guide

### 1) Upload Voice Note (FormData)

```javascript
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

export async function uploadVoiceNote(audioBlob, accessToken) {
	const formData = new FormData();
	formData.append('audio_file', audioBlob, 'recording.webm');
	formData.append('title', 'My New Recording');

	const response = await axios.post(`${API_BASE}/notes/`, formData, {
		headers: {
			Authorization: `Bearer ${accessToken}`,
			'Content-Type': 'multipart/form-data'
		}
	});

	return response.data;
}
```

### 2) Display Action Items Safely

```jsx
{note.action_items?.length > 0 ? (
	<ul>
		{note.action_items.map((item, index) => (
			<li key={index}>✅ {item}</li>
		))}
	</ul>
) : (
	<p>No action items detected yet.</p>
)}
```

### 3) Refresh Access Token

```javascript
const response = await axios.post('http://127.0.0.1:8000/api/auth/token/refresh/', {
	refresh: refreshToken
});
const newAccessToken = response.data.access;
```

---

## 🔒 Security & Behavior Notes

- Global DRF default permission is `IsAuthenticated`.
- Notes list is user-scoped on backend (`request.user` filter).
- Owner is set server-side during note creation.
- Logout blacklists refresh tokens.
- AI processing failures are logged but do not fail note creation.

---

## 🧪 Testing

```bash
uv run python manage.py check
uv run python manage.py test users -v 2
uv run python manage.py test api -v 2
uv run python manage.py test -v 2
```

---

## 🚀 Local Setup

```bash
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py runserver
```

Required `.env` keys:
- `DJANGO_SECRET_KEY`
- `GEMINI_API_KEY`

---

## ⚠️ Current Constraints

- `DEBUG=True` is currently hardcoded in settings.
- `ALLOWED_HOSTS` is currently empty.
- `CORS_ALLOWED_ORIGINS` is currently hardcoded for localhost ports.
- SQLite is used by default; use PostgreSQL for production.

---

## ✅ Stability Baseline

Validated baseline (all tests passing) exists in git history with stabilization, log-ignore, and documentation commits.


