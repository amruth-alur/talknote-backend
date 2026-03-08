import whisper
import os
from django.conf import settings

# Load the model once (Singleton) to save memory
# "base" is a good balance of speed vs accuracy for laptops
MODEL = whisper.load_model("base")

class TranscriptionService:
    @staticmethod
    def transcribe_audio(audio_path):
        """
        Takes a file path, runs Whisper AI, and returns text.
        """
        try:
            # Construct full path if needed
            full_path = os.path.join(settings.MEDIA_ROOT, str(audio_path))
            
            print(f"🤖 AI Starting transcription for: {full_path}")
            
            # The Magic Line: Runs the AI
            result = MODEL.transcribe(full_path)
            
            text = result['text'].strip()
            print(f"✅ Transcription Success: {text[:50]}...")
            return text
            
        except Exception as e:
            print(f"❌ AI Error: {str(e)}")
            return None