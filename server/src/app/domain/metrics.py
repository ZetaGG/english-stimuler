def words_per_minute(word_count: int, duration_seconds: float) -> float:
    if word_count < 0:
        raise ValueError("word_count must be non-negative")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    return round(word_count / (duration_seconds / 60.0), 1)
