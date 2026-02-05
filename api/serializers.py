from rest_framework import serializers
from .models import Note

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'title', 'audio_file', 'transcript', 'summary', 'action_items', 'created_at']
        read_only_fields = ['id', 'created_at']