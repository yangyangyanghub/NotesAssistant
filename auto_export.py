#!/usr/bin/env python3
"""
Auto-export WeChat favorites.

Strategy: always double-click the FIRST visible item, export it,
then scroll down by one item. Verify scroll worked by comparing
list screenshots before/after.
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

import pyautogui
from PIL import Image

# === Config ===
OUTPUT_DIR = "output/全部收藏"
ITEM_X = 420         # logical x for clicking item cards
ITEM_Y = 125         # logical y of the first visible item
LIST_AREA_X = 380    # x to click list area for focus
LIST_AREA_Y = 300    # y to click list area for focus
SCROLL_AMOUNT = 10   # per scroll() call
SCROLL_CALLS = 5     # calls per item (total = 50 units)


# === Helpers ===
def activate():
    subprocess.run(
        ['osascript', '-e', 'tell application "WeChat" to activate'],
        capture_output=True, text=True,
    )


def win_count():
    r = subprocess.run(
        ['osascript', '-e',
         'tell application "System Events" to tell process "WeChat" to count of windows'],
        capture_output=True, text=True, timeout=10,
    )
    return int(r.stdout.strip())


def get_bounds():
    time.sleep(0.5)
    script = (
        'tell application "System Events" to tell process "WeChat"\n'
        'set p to position of front window\nset s to size of front window\n'
        'return "" & (item 1 of p) & "," & (item 2 of p) & "," '
        '& (item 1 of s) & "," & (item 2 of s)\nend tell'
    )
    r = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    parts = [int(x.strip()) for x in r.stdout.strip().split(',')]
    return tuple(parts[:4])


def close_win():
    subprocess.run(
        ['osascript', '-e',
         'tell application "System Events" to tell process "WeChat" '
         'to keystroke "w" using command down'],
        capture_output=True, text=True,
    )


def focus_list():
    """Click on the list area to give it scroll focus."""
    activate()
    time.sleep(0.2)
    # Single click on list area (not double-click, to avoid opening item)
    pyautogui.click(LIST_AREA_X, LIST_AREA_Y)
    time.sleep(0.2)


def scroll_down_one():
    """Scroll the list down by one item."""
    # First ensure list area has focus
    focus_list()
    # Now scroll
    for _ in range(SCROLL_CALLS):
        pyautogui.scroll(-SCROLL_AMOUNT)
        time.sleep(0.08)
    time.sleep(0.3)


def list_snapshot():
    """Snapshot the first item area for comparison."""
    # Capture the area where the first item card is (Retina 2x)
    return pyautogui.screenshot(region=(260, 70, 220, 150))


def snapshots_differ(a, b):
    """Check if two snapshots are meaningfully different."""
    a_small = a.resize((32, 32)).convert("L")
    b_small = b.resize((32, 32)).convert("L")
    pa, pb = list(a_small.getdata()), list(b_small.getdata())
    diff = sum(abs(x - y) for x, y in zip(pa, pb))
    avg_diff = diff / len(pa)
    return avg_diff > 3  # threshold: avg pixel diff > 3


def long_screenshot(bounds):
    """Scroll detail window and stitch screenshots."""
    x, y, w, h = bounds
    pyautogui.moveTo(x + w // 2, y + h // 2)
    time.sleep(0.2)

    def _hash(img):
        s = img.resize((8, 8)).convert("L")
        return list(s.getdata())

    def _similar(a, b):
        ha, hb = _hash(a), _hash(b)
        return sum(abs(x - y) for x, y in zip(ha, hb)) < 300

    shots = []
    prev = None
    same = 0
    for page in range(20):
        shot = pyautogui.screenshot(region=bounds)
        if prev and _similar(shot, prev):
            same += 1
            if same >= 2:
                break
        else:
            same = 0
            shots.append(shot)
        prev = shot
        if page < 19:
            pyautogui.scroll(-5)
            time.sleep(0.4)

    if not shots:
        return pyautogui.screenshot(region=bounds), 1
    if len(shots) == 1:
        return shots[0], 1

    overlap = int(shots[0].height * 0.1)
    total_h = shots[0].height + sum(s.height - overlap for s in shots[1:])
    result = Image.new("RGB", (shots[0].width, total_h))
    yp = 0
    for i, s in enumerate(shots):
        if i == 0:
            result.paste(s, (0, 0))
            yp = s.height
        else:
            c = s.crop((0, overlap, s.width, s.height))
            result.paste(c, (0, yp))
            yp += c.height
    return result, len(shots)


def export_item(idx):
    """Export the first visible item in the list."""
    item_dir = os.path.join(OUTPUT_DIR, f'{idx:03d}')
    meta_path = os.path.join(item_dir, 'meta.json')
    os.makedirs(item_dir, exist_ok=True)

    activate()
    time.sleep(0.3)

    before = win_count()
    pyautogui.doubleClick(ITEM_X, ITEM_Y)
    time.sleep(1.5)
    after = win_count()

    if after <= before:
        pyautogui.screenshot().save(os.path.join(item_dir, 'screenshot.png'))
        meta = {
            'index': idx,
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'open_failed': True,
        }
        with open(meta_path, 'w') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f'  [{idx:03d}] no window — list screenshot saved')
        return

    bounds = get_bounds()
    if not bounds:
        close_win()
        return

    # Long screenshot
    img, pages = long_screenshot(bounds)
    img.save(os.path.join(item_dir, 'screenshot.png'))

    # Copy text (scroll back to top first)
    pyautogui.moveTo(bounds[0] + bounds[2] // 2, bounds[1] + bounds[3] // 2)
    for _ in range(30):
        pyautogui.scroll(10)
    time.sleep(0.2)
    pyautogui.hotkey('command', 'a')
    time.sleep(0.2)
    pyautogui.hotkey('command', 'c')
    time.sleep(0.2)
    r = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
    text = (r.stdout or '').strip()
    if text:
        with open(os.path.join(item_dir, 'content.txt'), 'w', encoding='utf-8') as f:
            f.write(text)

    urls = re.findall(r'https?://[^\s<>"\'）》，。]+', text) if text else []

    close_win()
    time.sleep(0.5)

    meta = {
        'index': idx,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'has_text': len(text) > 0,
        'text_length': len(text),
        'urls': urls,
        'screenshot_pages': pages,
    }
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f'  [{idx:03d}] ✓ ({pages}p, {len(text)}c)')


def main():
    max_items = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    activate()
    time.sleep(0.5)
    pyautogui.click(137, 150)  # 全部收藏
    time.sleep(0.5)

    # Scroll to top first
    pyautogui.moveTo(LIST_AREA_X, LIST_AREA_Y)
    for _ in range(30):
        pyautogui.scroll(10)
        time.sleep(0.05)
    time.sleep(0.5)

    print(f"Exporting up to {max_items} items from 全部收藏")
    print(f"Output: {os.path.abspath(OUTPUT_DIR)}\n")

    no_scroll_count = 0

    for idx in range(max_items):
        snap_before = list_snapshot()

        print(f'Item {idx}:')
        export_item(idx)

        # Scroll down one item
        scroll_down_one()

        # Verify scroll worked
        snap_after = list_snapshot()
        if snapshots_differ(snap_before, snap_after):
            no_scroll_count = 0
            print(f'  → scrolled OK')
        else:
            no_scroll_count += 1
            print(f'  → scroll may have failed ({no_scroll_count}/5)')
            if no_scroll_count >= 5:
                print(f'\nList not scrolling — reached end after {idx + 1} items.')
                break
            # Try extra scroll
            scroll_down_one()

    print(f'\n=== Done: {idx + 1} items exported ===')


if __name__ == "__main__":
    main()
