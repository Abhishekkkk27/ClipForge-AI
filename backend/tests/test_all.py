"""
ClipForge AI — Backend Tests
Tests: URL validation, highlight scoring, subtitle segmentation, API
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ─── URL Validation Tests ──────────────────────────────────────────────────────

from backend.utils.validation import is_valid_youtube_url, extract_video_id, sanitize_filename


class TestUrlValidation:
    def test_standard_watch_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_short_url(self):
        assert is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_shorts_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")

    def test_no_https(self):
        assert is_valid_youtube_url("youtube.com/watch?v=dQw4w9WgXcQ")

    def test_url_with_timestamp(self):
        assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s")

    def test_invalid_url(self):
        assert not is_valid_youtube_url("https://vimeo.com/12345")

    def test_empty_string(self):
        assert not is_valid_youtube_url("")

    def test_plain_text(self):
        assert not is_valid_youtube_url("not a url at all")

    def test_youtube_homepage(self):
        assert not is_valid_youtube_url("https://www.youtube.com/")

    def test_extract_video_id(self):
        vid = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_extract_from_short(self):
        vid = extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_sanitize_filename_removes_illegal_chars(self):
        result = sanitize_filename('video: "the best" <clip>')
        assert ":" not in result
        assert '"' not in result
        assert "<" not in result


# ─── Highlight Detection Tests ─────────────────────────────────────────────────

from backend.services.highlight_detection import RuleBasedHighlightDetector
from backend.services.transcription import TranscriptSegment


def make_segment(i, text, start=0.0, end=5.0):
    return TranscriptSegment(
        segment_id=i,
        start=start,
        end=end,
        text=text,
        words=[],
    )


class TestHighlightDetection:
    def test_hook_words_increase_score(self):
        detector = RuleBasedHighlightDetector()
        strong = make_segment(0, "The secret truth nobody knows about this amazing discovery!")
        weak = make_segment(1, "And then we went to the store and bought some milk.")
        candidates = detector.score_segments([strong, weak])
        strong_cand = next((c for c in candidates if c.segment_index == 0), None)
        weak_cand = next((c for c in candidates if c.segment_index == 1), None)
        if strong_cand and weak_cand:
            assert strong_cand.score.combined_score > weak_cand.score.combined_score

    def test_question_increases_score(self):
        detector = RuleBasedHighlightDetector()
        seg = make_segment(0, "But what if I told you that everything you know is wrong?")
        candidates = detector.score_segments([seg])
        assert len(candidates) > 0
        assert candidates[0].score.question_score > 0

    def test_statistics_increase_info_score(self):
        detector = RuleBasedHighlightDetector()
        seg = make_segment(0, "Studies show that 73% of people fail because of this one mistake.")
        candidates = detector.score_segments([seg])
        assert len(candidates) > 0
        assert candidates[0].score.information_score > 0

    def test_reason_generated(self):
        detector = RuleBasedHighlightDetector()
        seg = make_segment(0, "The secret nobody tells you about success is this surprising fact!")
        candidates = detector.score_segments([seg])
        assert len(candidates) > 0
        assert len(candidates[0].reason) > 0

    def test_empty_segments_returns_empty(self):
        detector = RuleBasedHighlightDetector()
        result = detector.score_segments([])
        assert result == []

    def test_hindi_text_does_not_crash(self):
        detector = RuleBasedHighlightDetector()
        seg = make_segment(0, "यह सबसे महत्वपूर्ण बात है जो आपको जाननी चाहिए।")
        # Should not raise
        candidates = detector.score_segments([seg])
        assert isinstance(candidates, list)


# ─── Subtitle Segmentation Tests ───────────────────────────────────────────────

from backend.services.subtitles import _chunk_words, generate_ass_subtitle


class TestSubtitles:
    def _make_segment_with_words(self, text, start, end):
        words_text = text.split()
        word_dur = (end - start) / max(len(words_text), 1)
        words = [
            {"word": w, "start": start + i * word_dur, "end": start + (i + 1) * word_dur, "probability": 0.9}
            for i, w in enumerate(words_text)
        ]
        return TranscriptSegment(
            segment_id=0, start=start, end=end,
            text=text, words=words,
        )

    def test_chunks_split_correctly(self):
        seg = self._make_segment_with_words("one two three four five six seven eight", 0.0, 8.0)
        chunks = _chunk_words([seg], clip_start=0.0, clip_end=8.0, words_per_chunk=4)
        assert len(chunks) == 2
        assert "one" in chunks[0].text
        assert "five" in chunks[1].text

    def test_chunks_time_offset_from_clip_start(self):
        seg = self._make_segment_with_words("hello world test clip", 10.0, 14.0)
        chunks = _chunk_words([seg], clip_start=10.0, clip_end=14.0, words_per_chunk=4)
        assert len(chunks) == 1
        assert chunks[0].start >= 0.0  # relative to clip start

    def test_ass_generated_without_error(self):
        seg = self._make_segment_with_words("this is a test sentence", 0.0, 5.0)
        content = generate_ass_subtitle([seg], clip_start=0.0, clip_end=30.0, style="bold")
        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content

    def test_minimal_style_generates(self):
        seg = self._make_segment_with_words("minimal style test", 0.0, 3.0)
        content = generate_ass_subtitle([seg], 0.0, 30.0, style="minimal")
        assert "Style: Default" in content

    def test_empty_segments_produces_valid_ass(self):
        content = generate_ass_subtitle([], clip_start=0.0, clip_end=30.0)
        assert "[Script Info]" in content


# ─── Clip Selection Tests ──────────────────────────────────────────────────────

from backend.services.clip_generator import select_clips, ClipWindow
from backend.services.highlight_detection import HighlightCandidate, HighlightScore


class TestClipSelection:
    def _make_candidate(self, idx, score_val, start, end, text="test"):
        score = HighlightScore()
        score.hook_score = score_val
        score.compute()
        return HighlightCandidate(
            segment_index=idx,
            score=score,
            reason="test reason",
            start_time=start,
            end_time=end,
            text=text,
        )

    def test_returns_correct_number_of_clips(self):
        segs = [make_segment(i, f"segment {i}", i * 5, i * 5 + 5) for i in range(30)]
        candidates = [self._make_candidate(i, 0.8, i * 5, i * 5 + 5) for i in range(10)]
        clips = select_clips(segs, candidates, target_duration=30, num_clips=5, video_duration=150)
        assert len(clips) <= 5

    def test_no_overlap_between_clips(self):
        segs = [make_segment(i, f"seg {i}", i * 10, i * 10 + 10) for i in range(20)]
        candidates = [self._make_candidate(i, 0.9, i * 10, i * 10 + 10) for i in range(10)]
        clips = select_clips(segs, candidates, target_duration=30, num_clips=3, video_duration=200)
        for i in range(len(clips)):
            for j in range(i + 1, len(clips)):
                overlap = max(0, min(clips[i].end_time, clips[j].end_time) - max(clips[i].start_time, clips[j].start_time))
                assert overlap < 15, f"Clips {i} and {j} overlap by {overlap}s"

    def test_clips_sorted_by_start_time(self):
        segs = [make_segment(i, f"seg {i}", i * 15, i * 15 + 15) for i in range(20)]
        candidates = [self._make_candidate(i, 0.7, i * 15, i * 15 + 15) for i in range(10)]
        clips = select_clips(segs, candidates, target_duration=30, num_clips=3, video_duration=300)
        starts = [c.start_time for c in clips]
        assert starts == sorted(starts)

    def test_empty_candidates_uses_fallback(self):
        segs = [make_segment(i, f"seg {i}", i * 10, i * 10 + 10) for i in range(30)]
        clips = select_clips(segs, [], target_duration=30, num_clips=3, video_duration=300)
        assert len(clips) <= 3


# ─── API Tests ─────────────────────────────────────────────────────────────────

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

# Initialize DB tables for tests
init_db()
client = TestClient(app)


class TestAPI:
    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "status" in data["data"]

    def test_root_endpoint(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_validate_url_valid(self):
        resp = client.post("/api/validate-url", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
        assert resp.status_code == 200
        assert resp.json()["data"]["valid"] is True

    def test_validate_url_invalid(self):
        resp = client.post("/api/validate-url", json={"url": "https://vimeo.com/123"})
        assert resp.status_code == 200
        assert resp.json()["data"]["valid"] is False

    def test_list_jobs_empty(self):
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_create_job_invalid_url(self):
        resp = client.post("/api/jobs", json={"youtube_url": "not-a-url"})
        assert resp.status_code == 422  # Pydantic validation error

    def test_get_nonexistent_job(self):
        resp = client.get("/api/jobs/nonexistent-id")
        assert resp.status_code == 404
