"""
ClipForge AI — Audio Extraction
Extracts mono 16 kHz WAV audio from video for Whisper transcription.
"""

from pathlib import Path
from backend import config
from backend.utils.ffmpeg import run_ffmpeg
from backend.utils.logger import get_logger

log = get_logger("audio")


def extract_audio(video_path: Path, job_id: str) -> Path:
    """
    Extract audio from video_path → WAV (mono, 16 kHz).
    Returns the path to the WAV file.
    """
    output_dir = config.AUDIO_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / "audio.wav"

    log.info("[JOB %s] Extracting audio from: %s", job_id, video_path)

    run_ffmpeg([
        "-y",                     # overwrite output
        "-i", str(video_path),
        "-vn",                    # no video
        "-acodec", "pcm_s16le",   # WAV format
        "-ar", "16000",           # 16 kHz sample rate
        "-ac", "1",               # mono
        str(audio_path),
    ])

    log.info("[JOB %s] Audio extracted to: %s", job_id, audio_path)
    return audio_path
