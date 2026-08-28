"""
ClipForge AI — Rule-Based Highlight Detection
Scores transcript segments for interest/virality potential.
Architecture is modular — swap RuleBasedHighlightDetector for an LLM-based one later.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict

from backend.services.transcription import TranscriptSegment
from backend.utils.logger import get_logger

log = get_logger("highlight_detection")

# ─── Vocabulary Lists ──────────────────────────────────────────────────────────

HOOK_WORDS = [
    "secret", "truth", "actually", "surprising", "shocking", "unbelievable",
    "never", "always", "everyone", "nobody", "nobody knows", "you need",
    "you should", "listen", "wait", "but here", "here's", "this is why",
    "the reason", "the truth", "the secret", "the key", "this changes",
    "changed my", "life-changing", "game changer", "game-changing",
]

EMOTION_WORDS = [
    "amazing", "incredible", "awesome", "terrible", "horrible", "disgusting",
    "beautiful", "tragic", "heartbreaking", "hilarious", "funny", "sad",
    "angry", "excited", "love", "hate", "fear", "brave", "brilliant",
    "stupid", "genius", "crazy", "insane", "mind-blowing", "epic",
    "devastating", "inspiring", "powerful", "weak", "strong",
]

SURPRISE_WORDS = [
    "actually", "turns out", "in fact", "surprisingly", "unexpectedly",
    "but wait", "here's the thing", "plot twist", "you won't believe",
    "believe it or not", "little known", "most people don't",
    "what if i told you", "contrary to", "opposite",
]

PUNCHLINE_WORDS = [
    "so the answer is", "bottom line", "the point is", "in conclusion",
    "what this means", "takeaway", "key insight", "remember this",
    "most important", "most critical", "crucial", "essential",
]

INFORMATION_PATTERNS = [
    r"\d+%",                       # percentages
    r"\$[\d,]+",                   # money
    r"\d+ (times|x)",              # multipliers
    r"(study|research|science|data|statistics|according to|found that)",
    r"(how to|step \d|first|second|third|finally|tip \d)",
    r"(number \d|#\d|step \d)",
]


@dataclass
class HighlightScore:
    hook_score: float = 0.0
    emotion_score: float = 0.0
    information_score: float = 0.0
    surprise_score: float = 0.0
    question_score: float = 0.0
    punchline_score: float = 0.0
    completeness_score: float = 0.0
    combined_score: float = 0.0

    def compute(self) -> float:
        self.combined_score = (
            0.20 * self.hook_score
            + 0.15 * self.emotion_score
            + 0.15 * self.information_score
            + 0.15 * self.surprise_score
            + 0.10 * self.question_score
            + 0.15 * self.punchline_score
            + 0.10 * self.completeness_score
        )
        return self.combined_score


@dataclass
class HighlightCandidate:
    segment_index: int
    score: HighlightScore
    reason: str
    start_time: float
    end_time: float
    text: str


class HighlightDetector(ABC):
    """Interface for highlight detectors."""

    @abstractmethod
    def score_segments(
        self,
        segments: List[TranscriptSegment],
    ) -> List[HighlightCandidate]:
        ...


class RuleBasedHighlightDetector(HighlightDetector):
    """
    Rule-based scoring using vocabulary lists, patterns, and structural signals.
    No external API required.
    """

    def score_segments(
        self,
        segments: List[TranscriptSegment],
    ) -> List[HighlightCandidate]:
        candidates: List[HighlightCandidate] = []

        for i, seg in enumerate(segments):
            text_lower = seg.text.lower()
            score = HighlightScore()

            # ── Hook score ────────────────────────────────────────────
            hook_hits = sum(1 for w in HOOK_WORDS if w in text_lower)
            score.hook_score = min(hook_hits / 2.0, 1.0)

            # Position bonus: segments near start/end of video get a slight boost
            # (these are often intro hooks or strong conclusions)
            total = len(segments)
            if i < total * 0.15 or i > total * 0.85:
                score.hook_score = min(score.hook_score + 0.2, 1.0)

            # ── Emotion score ─────────────────────────────────────────
            emotion_hits = sum(1 for w in EMOTION_WORDS if w in text_lower)
            score.emotion_score = min(emotion_hits / 3.0, 1.0)

            # Exclamation / caps boost
            if "!" in seg.text:
                score.emotion_score = min(score.emotion_score + 0.15, 1.0)
            if sum(1 for c in seg.text if c.isupper()) > len(seg.text) * 0.3:
                score.emotion_score = min(score.emotion_score + 0.1, 1.0)

            # ── Information score ─────────────────────────────────────
            info_hits = sum(
                1 for p in INFORMATION_PATTERNS
                if re.search(p, text_lower)
            )
            score.information_score = min(info_hits / 3.0, 1.0)

            # ── Surprise score ────────────────────────────────────────
            surp_hits = sum(1 for w in SURPRISE_WORDS if w in text_lower)
            score.surprise_score = min(surp_hits / 2.0, 1.0)

            # ── Question score ────────────────────────────────────────
            q_count = seg.text.count("?")
            score.question_score = min(q_count * 0.4, 1.0)

            # ── Punchline score ───────────────────────────────────────
            punch_hits = sum(1 for w in PUNCHLINE_WORDS if w in text_lower)
            score.punchline_score = min(punch_hits / 2.0, 1.0)

            # ── Completeness score ────────────────────────────────────
            # Prefer segments that start with a capital letter and end with punctuation
            starts_capital = int(bool(seg.text and seg.text[0].isupper()))
            ends_punct = int(bool(seg.text and seg.text[-1] in ".!?"))
            word_count = len(seg.text.split())
            length_score = min(word_count / 20.0, 1.0)  # 20+ words = full score
            score.completeness_score = (starts_capital * 0.3 + ends_punct * 0.3 + length_score * 0.4)

            # ── Combined ──────────────────────────────────────────────
            combined = score.compute()

            # Skip very low scores
            if combined < 0.05:
                continue

            reason = _generate_reason(score, seg.text)

            candidates.append(HighlightCandidate(
                segment_index=i,
                score=score,
                reason=reason,
                start_time=seg.start,
                end_time=seg.end,
                text=seg.text,
            ))

        log.info("Scored %d candidates from %d segments", len(candidates), len(segments))
        return candidates


def _generate_reason(score: HighlightScore, text: str) -> str:
    """Generate a human-readable explanation for why the clip was selected."""
    reasons = []

    if score.hook_score > 0.5:
        reasons.append("strong opening hook")
    if score.emotion_score > 0.5:
        reasons.append("high emotional intensity")
    if score.information_score > 0.5:
        reasons.append("high information density")
    if score.surprise_score > 0.4:
        reasons.append("surprising statement")
    if score.question_score > 0.3:
        reasons.append("engaging question")
    if score.punchline_score > 0.4:
        reasons.append("clear punchline or conclusion")
    if score.completeness_score > 0.7:
        reasons.append("complete and well-formed thought")

    if not reasons:
        reasons.append("notable content")

    return "Contains a " + ", ".join(reasons) + "."
