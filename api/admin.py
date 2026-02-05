from django.contrib import admin
from .models import Note

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    # This controls what columns you see in the list
    list_display = ('title', 'created_at', 'has_audio', 'has_transcript')
    list_filter = ('created_at',)
    search_fields = ('title', 'transcript')

    # Helper methods to show status icons
    def has_audio(self, obj):
        return bool(obj.audio_file)
    has_audio.boolean = True
    
    def has_transcript(self, obj):
        return bool(obj.transcript)
    has_transcript.boolean = True