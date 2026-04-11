# wechat_favorites_exporter/config.py
import json
import os
import random
import time

CLICK_DELAY_MEAN = 1.5
CLICK_DELAY_STD = 0.3
CLICK_DELAY_MIN = 0.8
SCROLL_DELAY = 0.5
WINDOW_TIMEOUT = 5.0
DUPLICATE_THRESHOLD = 5
END_DETECTION_COUNT = 3
LONG_SCREENSHOT_OVERLAP = 0.2
OUTPUT_DIR = "output"

CATEGORIES = [
    "全部收藏", "最近使用", "链接", "图片与视频",
    "笔记", "文件", "聊天记录", "位置", "小程序",
]


def random_delay():
    delay = max(CLICK_DELAY_MIN, random.gauss(CLICK_DELAY_MEAN, CLICK_DELAY_STD))
    time.sleep(delay)


def save_progress(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_progress(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
