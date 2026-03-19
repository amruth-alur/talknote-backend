import json
import logging
import os
import time

import whisper
from django.conf import settings
from google import genai


logger = logging.getLogger(__name__)


try:
    logger.info("Loading Whisper model into memory...")
    MODEL = whisper.load_model("base")
    logger.info("Whisper model loaded successfully")
except Exception:
    MODEL = None
    logger.exception("Failed to load Whisper model")


def _build_genai_client():
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        logger.error("GEMINI_API_KEY is missing in settings/environment")
        return None
    return genai.Client(api_key=api_key)


GENAI_CLIENT = _build_genai_client()


def _extract_json_payload(raw_text: str) -> dict:
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM response is not a JSON object")
    return data


class TranscriptionService:
    @staticmethod
    def transcribe_audio(audio_path: str) -> str | None:
        if not audio_path:
            return None
        if MODEL is None:
            logger.error("Whisper model unavailable; cannot transcribe audio")
            return None

        try:
            full_path = os.path.join(settings.MEDIA_ROOT, str(audio_path))
            logger.info("Starting transcription for: %s", full_path)

            result = MODEL.transcribe(full_path)
            text = result.get("text", "").strip()

            logger.info("Transcription successful (chars=%d)", len(text))
            return text or None
        except Exception:
            if settings.DEBUG:
                logger.exception("Transcription failed for path: %s", audio_path)
            else:
                logger.error("Transcription failed for path: %s", audio_path)
            return None


class LLMService:
    @staticmethod
    def analyze_transcript(transcript_text: str) -> dict | None:
        if not transcript_text:
            return None
        if GENAI_CLIENT is None:
            return {"summary": "AI service unavailable.", "action_items": []}

        prompt = f"""
Analyze the following voice note transcript.
Provide a short 1-sentence summary and a list of actionable tasks.
Return ONLY valid JSON in this exact format:
{{
  "summary": "One sentence summary",
  "action_items": ["Task 1", "Task 2"]
}}

Transcript:
"{transcript_text}"
""".strip()

        attempts = 2
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                response = GENAI_CLIENT.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )

                raw = (getattr(response, "text", None) or "").strip()
                data = _extract_json_payload(raw)

                summary = data.get("summary", "")
                action_items = data.get("action_items", [])

                if not isinstance(summary, str):
                    summary = str(summary)
                if not isinstance(action_items, list):
                    action_items = []

                return {
                    "summary": summary,
                    "action_items": action_items,
                }
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "LLM analysis attempt %d/%d failed: %s",
                    attempt,
                    attempts,
                    str(exc),
                )
                if attempt < attempts:
                    time.sleep(1.5)

        if settings.DEBUG and last_exc is not None:
            logger.error(
                "LLM analysis failed after %d attempts",
                attempts,
                exc_info=last_exc,
            )
        else:
            logger.error("LLM analysis failed after %d attempts", attempts)
        return {"summary": "Failed to generate summary.", "action_items": []}
