from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Note


User = get_user_model()


class NoteCreationIntegrationTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email="notes@example.com",
			password="StrongPass123!",
		)
		self.client.force_authenticate(user=self.user)
		self.url = "/api/notes/"

	def _audio_file(self):
		return SimpleUploadedFile(
			"sample.wav",
			b"RIFF....WAVEfmt ",
			content_type="audio/wav",
		)

	@patch("api.views.TranscriptionService.transcribe_audio")
	@patch("api.views.LLMService.analyze_transcript")
	def test_create_note_with_audio_success(self, mock_analyze, mock_transcribe):
		mock_transcribe.return_value = "Meeting transcript"
		mock_analyze.return_value = {
			"summary": "Team sync summary.",
			"action_items": ["Send recap", "Book follow-up"],
		}

		response = self.client.post(
			self.url,
			{"title": "Weekly Sync", "audio_file": self._audio_file()},
			format="multipart",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = Note.objects.get(id=response.data["id"])
		self.assertEqual(created.transcript, "Meeting transcript")
		self.assertEqual(created.summary, "Team sync summary.")
		self.assertEqual(created.action_items, ["Send recap", "Book follow-up"])

	@patch("api.views.TranscriptionService.transcribe_audio")
	@patch("api.views.LLMService.analyze_transcript")
	def test_create_note_persists_transcript_when_llm_fails(
		self, mock_analyze, mock_transcribe
	):
		mock_transcribe.return_value = "Transcript survives LLM failure"
		mock_analyze.side_effect = RuntimeError("Rate limit")

		response = self.client.post(
			self.url,
			{"title": "Failure Path", "audio_file": self._audio_file()},
			format="multipart",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = Note.objects.get(id=response.data["id"])
		self.assertEqual(created.transcript, "Transcript survives LLM failure")
		self.assertTrue(created.summary in [None, ""])
		self.assertEqual(created.action_items, [])

	@patch("api.views.TranscriptionService.transcribe_audio")
	def test_create_note_succeeds_when_transcription_fails(self, mock_transcribe):
		mock_transcribe.side_effect = RuntimeError("Whisper unavailable")

		response = self.client.post(
			self.url,
			{"title": "Audio with Error", "audio_file": self._audio_file()},
			format="multipart",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = Note.objects.get(id=response.data["id"])
		self.assertTrue(created.transcript in [None, ""])
		self.assertTrue(created.summary in [None, ""])
		self.assertEqual(created.action_items, [])

	def test_create_note_without_audio(self):
		response = self.client.post(self.url, {"title": "Text Note"}, format="multipart")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = Note.objects.get(id=response.data["id"])
		self.assertIsNone(created.audio_file.name if created.audio_file else None)
		self.assertTrue(created.transcript in [None, ""])

	def test_list_notes_is_user_scoped(self):
		other_user = User.objects.create_user(
			email="other@example.com",
			password="StrongPass123!",
		)
		Note.objects.create(user=self.user, title="Mine")
		Note.objects.create(user=other_user, title="Not Mine")

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["title"], "Mine")
