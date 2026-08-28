"""
ClipForge AI — Speech Transcription
Uses faster-whisper for local, free transcription.
Produces word-level and segment-level timestamps.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from backend import config
from backend.utils.logger import get_logger

log = get_logger("transcription")


@dataclass
class TranscriptSegment:
    segment_id: int
    start: float
    end: float
    text: str
    words: List[Dict[str, Any]]  # [{word, start, end, probability}]
    avg_logprob: float = 0.0
    no_speech_prob: float = 0.0


def transcribe_audio(
    audio_path: Path,
    job_id: str,
    language: Optional[str] = None,
) -> tuple[List[TranscriptSegment], str, Path]:
    """
    Transcribe audio using faster-whisper.
    Returns (segments, detected_language, transcript_json_path).
    """
    log.info("[JOB %s] Loading Whisper model: %s", job_id, config.WHISPER_MODEL)

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        )

    model = WhisperModel(
        config.WHISPER_MODEL,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )

    log.info("[JOB %s] Transcribing: %s", job_id, audio_path)

    transcribe_kwargs = {
        "word_timestamps": True,
        "vad_filter": True,           # skip silence
        "vad_parameters": {"min_silence_duration_ms": 500},
    }
    if language:
        transcribe_kwargs["language"] = language

    raw_segments, info = model.transcribe(str(audio_path), **transcribe_kwargs)

    detected_language = info.language
    log.info("[JOB %s] Detected language: %s (prob=%.2f)", job_id, detected_language, info.language_probability)

    segments: List[TranscriptSegment] = []
    for i, seg in enumerate(raw_segments):
        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3),
                })

        segments.append(TranscriptSegment(
            segment_id=i,
            start=round(seg.start, 3),
            end=round(seg.end, 3),
            text=seg.text.strip(),
            words=words,
            avg_logprob=round(seg.avg_logprob, 4),
            no_speech_prob=round(seg.no_speech_prob, 4),
        ))

    log.info("[JOB %s] Transcription complete: %d segments", job_id, len(segments))

    # Save transcript JSON
    transcript_dir = config.TRANSCRIPTS_DIR / job_id
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = transcript_dir / "transcript.json"

    transcript_data = {
        "language": detected_language,
        "segments": [asdict(s) for s in segments],
    }
    transcript_path.write_text(
        json.dumps(transcript_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return segments, detected_language, transcript_path
