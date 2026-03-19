from django.conf import settings
from django.db import models
import uuid

class Note(models.Model):
    # UUID is safer than ID (1, 2, 3) for public URLs
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes',
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200, default="New Voice Note")
    
    # This automatically saves audio files to a 'voice_notes' folder
    audio_file = models.FileField(upload_to='voice_notes/', blank=True, null=True)
    
    # We allow these to be empty initially, because AI takes time to generate them
    transcript = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    action_items = models.JSONField(default=list, blank=True) # Stores tasks as a list
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"