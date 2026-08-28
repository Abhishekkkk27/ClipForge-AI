# ClipForge AI

AI-powered YouTube short-form clip generator.

ClipForge AI takes a YouTube video URL, transcribes the video using faster-whisper, identifies interesting moments, creates approximately 30-second vertical clips, adds subtitles, and provides the finished clips for preview and download.

No paid AI API is required for the core application.

## Features

- YouTube URL validation
- Video metadata extraction
- Local speech-to-text with faster-whisper
- Automatic highlight detection
- Approximately 30-second clips
- 9:16 vertical video output
- Automatic subtitles
- Bold, Minimal, and Karaoke subtitle styles
- Highlight score and selection reason
- Real-time processing progress
- SQLite job tracking
- Individual clip downloads
- Download all clips as ZIP
- Modern responsive dashboard
- Local video processing

## Tech Stack

Frontend:
- Next.js 14
- React
- TypeScript
- Tailwind CSS

Backend:
- Python
- FastAPI
- SQLAlchemy
- SQLite

AI:
- faster-whisper
- Rule-based highlight detection

Video Processing:
- FFmpeg
- yt-dlp

## Architecture

```text
YouTube URL
     ↓
URL Validation
     ↓
Video Metadata
     ↓
Video Download
     ↓
Audio Extraction
     ↓
Whisper Transcription
     ↓
Highlight Detection
     ↓
Clip Selection
     ↓
9:16 Conversion
     ↓
Subtitle Generation
     ↓
Final MP4 Clips
     ↓
Preview / Download
