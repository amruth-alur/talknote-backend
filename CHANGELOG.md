# Changelog
## 2026-03-19

### Stabilization Baseline (`c3d5ce6`)

#### Authentication
+- Added custom email-based user model (`users.User`) with UUID primary key.
+- Added auth endpoints for register/login/me/change-password/logout.
+- Enabled JWT auth globally in DRF settings.
+- Enabled token blacklist app and refresh-token rotation.

#### Notes Domain
+- Added user ownership on notes via foreign key to custom user model.
+- Restricted note queryset to authenticated user.
+- Stamped note ownership server-side on create.
+- Protected AI-generated fields from client writes in serializer.

#### AI Integration
+- Migrated to `google-genai` SDK.
+- Added `LLMService` with structured JSON response parsing.
+- Added retries and fallback behavior for LLM failures.
+- Added logging and error handling for transcription and LLM paths.

#### Reliability and Observability
+- Added logging configuration with console and file handlers.
+- Added debug-aware exception logging behavior.
+- Improved note creation resilience so creation succeeds even if AI fails.

#### Testing
+- Added integration tests for notes flows including failure resilience.
+- Added comprehensive auth test coverage.
+- Test suite passing (`26` tests at stabilization time).

#### Routing and Config
+- Added `api/urls.py` and modularized project URL includes.
+- Added users app URLs and fixed namespace registration.
+- Added environment variable loading with `python-dotenv`.

### Repository Hygiene (`e07fc82`)
+- Added `logs/` to `.gitignore` to prevent runtime artifact tracking.
+