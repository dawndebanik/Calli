"""
Segment splitting utilities.
"""

from typing import List
from video_editor.models import TranscriptSegment, WordTimestamp


def split_segments_by_max_words(
    segments: List[TranscriptSegment],
    max_words: int
) -> List[TranscriptSegment]:
    """
    Split segments into smaller segments based on max words per segment.

    Requires word-level timestamps on input segments.

    Args:
        segments: List of TranscriptSegment objects with word timestamps
        max_words: Maximum words per segment

    Returns:
        List of split TranscriptSegment objects
    """
    if max_words <= 0:
        raise ValueError("max_words must be greater than 0")

    split_segments: List[TranscriptSegment] = []

    for segment in segments:
        if not segment.words:
            raise ValueError(
                "Word-level timestamps are required to split by max words."
            )

        words = [w for w in segment.words if w.word.strip()]
        if not words:
            continue

        for i in range(0, len(words), max_words):
            chunk = words[i:i + max_words]
            start = chunk[0].start
            end = chunk[-1].end
            text = " ".join(w.word.strip() for w in chunk).strip()

            split_segments.append(
                TranscriptSegment(
                    start=start,
                    end=end,
                    text=text,
                    words=chunk
                )
            )

    return split_segments





