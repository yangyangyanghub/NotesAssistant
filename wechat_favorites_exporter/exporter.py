import json
import os
import platform
import time
from datetime import datetime

import pyautogui
from PIL import Image

from wechat_favorites_exporter import content_extractor, window_manager
from wechat_favorites_exporter.calibrator import CalibrationData
from wechat_favorites_exporter.config import LONG_SCREENSHOT_OVERLAP, WINDOW_TIMEOUT, random_delay

_IS_MACOS = platform.system() == "Darwin"
_MODIFIER_KEY = "command" if _IS_MACOS else "ctrl"


def should_skip(index: int, preview: dict, output_dir: str) -> bool:
    item_dir = os.path.join(output_dir, f"{index:03d}")
    meta_path = os.path.join(item_dir, "meta.json")
    if not os.path.exists(meta_path):
        return False
    with open(meta_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    existing_preview = existing.get("preview", {})
    return (existing_preview.get("title") == preview.get("title")
            and existing_preview.get("date") == preview.get("date"))


def create_item_dir(output_dir: str, index: int) -> str:
    item_dir = os.path.join(output_dir, f"{index:03d}")
    os.makedirs(item_dir, exist_ok=True)
    return item_dir


def save_item_meta(item_dir: str, meta: dict) -> None:
    path = os.path.join(item_dir, "meta.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def build_meta(
    index: int, category: str, preview: dict,
    text: str | None = None, urls: list[str] | None = None,
    image_hash: str = "", open_failed: bool = False,
    skipped_detail: bool = False, screenshot_pages: int = 1,
    error: str | None = None,
) -> dict:
    return {
        "index": index, "category": category,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "has_text": text is not None and len(text) > 0,
        "urls": urls or [], "open_failed": open_failed,
        "skipped_detail": skipped_detail, "preview": preview,
        "error": error, "image_hash": image_hash,
        "screenshot_pages": screenshot_pages,
    }


def export_one_item(
    index: int, cal: CalibrationData, category: str,
    output_dir: str, prev_hash: str | None,
) -> dict | None:
    item_dir = create_item_dir(output_dir, index)

    # Step 1: Screenshot list item for preview OCR
    list_item_bounds = (cal.click_x - 300, cal.click_y - 40, 600, 80)
    list_img = content_extractor.capture_window_screenshot(list_item_bounds)
    preview = content_extractor.ocr_extract_preview(list_img)

    # Step 1b: Check if preview sufficient
    if content_extractor.is_preview_sufficient(preview):
        list_img.save(os.path.join(item_dir, "screenshot.png"))
        img_hash = content_extractor.compute_image_hash(list_img)
        meta = build_meta(index=index, category=category, preview=preview,
                         image_hash=img_hash, skipped_detail=True)
        save_item_meta(item_dir, meta)
        return meta

    # Step 2: Click item
    win_count = window_manager.get_wechat_window_count()
    pyautogui.click(cal.click_x, cal.click_y)

    # Step 3: Wait for new window
    if not window_manager.wait_for_new_window(win_count, timeout=WINDOW_TIMEOUT):
        list_img.save(os.path.join(item_dir, "screenshot.png"))
        img_hash = content_extractor.compute_image_hash(list_img)
        meta = build_meta(index=index, category=category, preview=preview,
                         image_hash=img_hash, open_failed=True)
        save_item_meta(item_dir, meta)
        return meta

    # Step 4: Wait for content
    random_delay()

    # Step 5: Get window bounds
    bounds = window_manager.get_front_window_bounds()
    if bounds is None:
        window_manager.close_front_window()
        meta = build_meta(index=index, category=category, preview=preview,
                         open_failed=True, error="Could not get window bounds")
        save_item_meta(item_dir, meta)
        return meta

    # Step 6: Long screenshot
    screenshots = []
    prev_shot = None
    consecutive_similar = 0
    for page in range(20):
        shot = content_extractor.capture_window_screenshot(bounds)
        if prev_shot is not None and content_extractor.images_are_similar(shot, prev_shot):
            consecutive_similar += 1
            if consecutive_similar >= 2:
                break
        else:
            consecutive_similar = 0
            screenshots.append(shot)
        prev_shot = shot
        if page < 19:
            pyautogui.scroll(-5)
            time.sleep(0.3)

    if screenshots:
        overlap = int(bounds[3] * LONG_SCREENSHOT_OVERLAP) if len(screenshots) > 1 else 0
        final_img = content_extractor.stitch_screenshots(screenshots, overlap=overlap)
    else:
        final_img = content_extractor.capture_window_screenshot(bounds)

    final_img.save(os.path.join(item_dir, "screenshot.png"))

    # Step 7: Extract text
    pyautogui.hotkey(_MODIFIER_KEY, "a")
    time.sleep(0.2)
    pyautogui.hotkey(_MODIFIER_KEY, "c")
    time.sleep(0.2)
    text = content_extractor.extract_text_from_clipboard()
    if text:
        with open(os.path.join(item_dir, "content.txt"), "w", encoding="utf-8") as f:
            f.write(text)

    # Step 8: Extract URLs
    urls = content_extractor.extract_urls(text) if text else []

    # Step 9: Close window
    window_manager.close_front_window()

    img_hash = content_extractor.compute_image_hash(final_img)
    meta = build_meta(index=index, category=category, preview=preview,
                     text=text, urls=urls, image_hash=img_hash,
                     screenshot_pages=len(screenshots))
    save_item_meta(item_dir, meta)
    return meta
