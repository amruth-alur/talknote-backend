from rest_framework import viewsets, parsers
from .models import Note
from .serializers import NoteSerializer
from .services import TranscriptionService # Import your new service

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all().order_by('-created_at')
    serializer_class = NoteSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def perform_create(self, serializer):
        # 1. Save the file to the DB first
        note = serializer.save()
        
        # 2. If an audio file exists, run AI
        if note.audio_file:
            print("🎤 Audio detected, starting AI processing...")
            
            # Call our Service
            transcript = TranscriptionService.transcribe_audio(note.audio_file.name)
            
            # 3. Save the result back to the DB
            if transcript:
                note.transcript = transcript
                note.save()