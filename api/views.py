import logging

from django.conf import settings

from rest_framework import parsers, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Note
from .serializers import NoteSerializer
from .services import LLMService, TranscriptionService


logger = logging.getLogger(__name__)

class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    # 1. THE BOUNCER: Reject any request that doesn't have a valid JWT token
    permission_classes = [IsAuthenticated] 

    # 2. THE DATA SHIELD: Override the default list so users only see their own notes
    def get_queryset(self):
        """
        Instead of Note.objects.all(), we filter by the user attached to the token.
        """
        return Note.objects.filter(user=self.request.user).order_by('-created_at')

    # 3. THE OWNERSHIP STAMP: Attach the user to the note when saving
    def perform_create(self, serializer):
        # We pass user=self.request.user so the database knows exactly who owns it
        note = serializer.save(user=self.request.user)

        if not note.audio_file:
            logger.info("Note created without audio file: %s", note.id)
            return

        try:
            logger.info("Audio detected for note %s. Starting transcription.", note.id)
            transcript = TranscriptionService.transcribe_audio(note.audio_file.name)

            if not transcript:
                logger.warning("No transcript generated for note %s", note.id)
                return

            note.transcript = transcript
            note.save(update_fields=["transcript", "updated_at"])

            analysis = LLMService.analyze_transcript(transcript)
            if analysis:
                summary = analysis.get("summary", "")
                action_items = analysis.get("action_items", [])
                note.summary = summary if isinstance(summary, str) else str(summary)
                note.action_items = action_items if isinstance(action_items, list) else []

            note.save(update_fields=["transcript", "summary", "action_items", "updated_at"])
            logger.info("AI processing completed for note %s", note.id)
        except Exception as exc:
            if settings.DEBUG:
                logger.exception("AI processing failed for note %s", note.id)
            else:
                logger.warning(
                    "AI processing failed for note %s: %s",
                    note.id,
                    str(exc),
                )