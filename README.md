📘 TalkNote API Documentation
Base URL: http://127.0.0.1:8000/api
Current Version: v1
Authentication: Open (CORS enabled for localhost:5173)
1. Create & Upload Voice Note
This is the main endpoint used to upload audio recordings. It triggers the AI transcription automatically.
 * Endpoint: /notes/
 * Method: POST
 * Content-Type: multipart/form-data (⚠️ Crucial)
Request Body (FormData)
You must use FormData object, not raw JSON, because you are sending a binary file.
| Field | Type | Required | Description |
|---|---|---|---|
| audio_file | File | ✅ Yes | The audio file (.mp3, .wav, .webm, .m4a). |
| title | String | ❌ No | User-defined title. Defaults to "New Voice Note". |
Response (201 Created)
Returns the created note object. If the backend is connected to AI, the transcript field will be populated immediately.
{
    "id": "b4e0afad-0330-4522-a5c6-67bd7fafd839",
    "title": "Project Brainstorming",
    "audio_file": "http://127.0.0.1:8000/media/voice_notes/recording.mp3",
    "transcript": "Okay, so for the new feature we need to...",
    "summary": "",
    "action_items": [],
    "created_at": "2026-02-06T11:30:00Z"
}

2. List All Notes
Fetch the history of all voice notes, sorted by newest first.
 * Endpoint: /notes/
 * Method: GET
Response (200 OK)
Returns an array of Note objects.
[
    {
        "id": "b4e0afad-...",
        "title": "Project Brainstorming",
        "audio_file": "http://127.0.0.1:8000/media/...",
        "transcript": "Okay, so for the new feature...",
        "created_at": "2026-02-06T11:30:00Z"
    },
    {
        "id": "a1c2d3e4-...",
        "title": "Grocery List",
        "audio_file": "http://127.0.0.1:8000/media/...",
        "transcript": "Milk, eggs, and bread.",
        "created_at": "2026-02-05T09:15:00Z"
    }
]

3. Get / Update / Delete a Note
Manage a specific note using its UUID.
 * Endpoint: /notes/<id>/ (e.g., /notes/b4e0afad-0330.../)
Supported Methods
 * GET: Retrieve full details of one note.
 * PUT / PATCH: Update details (e.g., if user edits the transcript manually).
   * Payload (JSON): { "title": "Updated Title", "transcript": "Corrected text" }
 * DELETE: Permanently remove the note and its audio file.
💾 Data Model Reference
| Field | Type | Description |
|---|---|---|
| id | UUID (String) | Unique Identifier (e.g., b4e0af...) |
| title | String | Max 200 chars. |
| audio_file | URL (String) | Full link to play the audio. |
| transcript | String | The raw text from Whisper AI. |
| summary | String | (Future) AI generated summary. Default: "". |
| action_items | Array of Strings | (Future) Extracted tasks. Default: []. |
| created_at | DateTime (ISO) | Timestamp of upload. |
⚛️ React Integration Guide 
How to Upload (Most Doubtful Part)
Since this involves files, you cannot just send a generic object. Use this function:
import axios from 'axios';

const uploadVoiceNote = async (audioBlob) => {
  // 1. Create the FormData package
  const formData = new FormData();
  
  // 'audio_file' matches the API field name exactly
  // 'recording.webm' is the filename the server will see
  formData.append('audio_file', audioBlob, 'recording.webm');
  
  // Optional: Add title
  formData.append('title', 'My New Recording');

  try {
    const response = await axios.post('http://127.0.0.1:8000/api/notes/', formData, {
      headers: {
        // Axios sets the correct boundary automatically when it sees FormData
        'Content-Type': 'multipart/form-data', 
      },
    });
    
    console.log('Upload Success:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('Upload Failed:', error.response?.data);
  }
};

How to Display Action Items (Safety)
The API guarantees action_items is an array (List), so you can safely .map() without checking for null.
// React Component Example
{note.action_items.length > 0 ? (
  <ul>
    {note.action_items.map((item, index) => (
      <li key={index}>✅ {item}</li>
    ))}
  </ul>
) : (
  <p>No action items detected yet.</p>
)}

