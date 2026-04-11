# tests/test_config.py
import json
import os
import time
from unittest.mock import patch

from wechat_favorites_exporter.config import (
    CATEGORIES,
    CLICK_DELAY_MEAN,
    CLICK_DELAY_MIN,
    CLICK_DELAY_STD,
    DUPLICATE_THRESHOLD,
    END_DETECTION_COUNT,
    LONG_SCREENSHOT_OVERLAP,
    OUTPUT_DIR,
    SCROLL_DELAY,
    WINDOW_TIMEOUT,
    load_progress,
    random_delay,
    save_progress,
)


def test_constants_exist():
    assert CLICK_DELAY_MEAN == 1.5
    assert CLICK_DELAY_STD == 0.3
    assert CLICK_DELAY_MIN == 0.8
    assert SCROLL_DELAY == 0.5
    assert WINDOW_TIMEOUT == 5.0
    assert DUPLICATE_THRESHOLD == 5
    assert END_DETECTION_COUNT == 3
    assert LONG_SCREENSHOT_OVERLAP == 0.2
    assert OUTPUT_DIR == "output"
    assert "全部收藏" in CATEGORIES
    assert len(CATEGORIES) == 9


def test_random_delay_within_bounds():
    delays = []
    with patch("time.sleep", side_effect=lambda d: delays.append(d)):
        for _ in range(100):
            random_delay()
    assert all(d >= CLICK_DELAY_MIN for d in delays)
    assert all(d < 10 for d in delays)
    assert len(set(round(d, 2) for d in delays)) > 1


def test_save_and_load_progress(tmp_path):
    progress_file = tmp_path / "progress.json"
    data = {
        "category": "链接",
        "last_completed_index": 42,
        "started_at": "2026-04-11T10:00:00",
        "updated_at": "2026-04-11T10:35:00",
    }
    save_progress(data, str(progress_file))
    loaded = load_progress(str(progress_file))
    assert loaded == data


def test_load_progress_missing_file(tmp_path):
    progress_file = tmp_path / "nonexistent.json"
    loaded = load_progress(str(progress_file))
    assert loaded is None
