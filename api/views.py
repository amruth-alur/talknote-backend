from rest_framework import viewsets, parsers
from .models import Note
from .serializers import NoteSerializer

class NoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Notes to be viewed or edited.
    automatically handles: GET, POST, PUT, DELETE
    """
    queryset = Note.objects.all().order_by('-created_at')
    serializer_class = NoteSerializer
    
    # Critical: This tells Django "Expect a File Upload, not just JSON"
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]