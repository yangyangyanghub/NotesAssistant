#!/usr/bin/env python3
"""
Auto-export WeChat favorites (Windows version).
Strategy: Process visible cards one by one, then scroll down for next page.
"""
import os
import platform
import sys
import time
from typing import Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        stdout_reconfigure = getattr(sys.stdout, 'reconfigure', None)
        if callable(stdout_reconfigure):
            stdout_reconfigure(encoding='utf-8')
    except Exception:
        pass
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

import pyautogui
import pyperclip

# === Platform Detection ===
_IS_MACOS = platform.system() == "Darwin"
_IS_WINDOWS = platform.system() == "Windows"
_MODIFIER_KEY = "command" if _IS_MACOS else "ctrl"

# === Config ===
OUTPUT_DIR = "output/全部收藏"
BASELINE_BOUNDS = (-8, -8, 1936, 1048)

# Known-good baseline absolute coordinates from the large-window layout.
FIRST_ITEM_X = 1040
FIRST_ITEM_Y = 158
ITEM_HEIGHT = 130
ITEMS_PER_PAGE = 7
LIST_AREA_X = 151
LIST_AREA_Y = 153
BTN_3DOTS_X = 1803
BTN_3DOTS_Y = 23
BTN_COPY_LINK_X = 1660
BTN_COPY_LINK_Y_CANDIDATES = [213, 238]

# Ratios derived from the known-good baseline; used to adapt to moved/resized windows.
_BASELINE_X = BASELINE_BOUNDS[0]
_BASELINE_Y = BASELINE_BOUNDS[1]
_BASELINE_W = BASELINE_BOUNDS[2]
_BASELINE_H = BASELINE_BOUNDS[3]

LIST_AREA_X_RATIO = (LIST_AREA_X - _BASELINE_X) / _BASELINE_W
LIST_AREA_Y_RATIO = (LIST_AREA_Y - _BASELINE_Y) / _BASELINE_H
FIRST_ITEM_X_RATIO = (FIRST_ITEM_X - _BASELINE_X) / _BASELINE_W
FIRST_ITEM_Y_RATIO = (FIRST_ITEM_Y - _BASELINE_Y) / _BASELINE_H
ITEM_HEIGHT_RATIO = ITEM_HEIGHT / _BASELINE_H
BTN_3DOTS_X_RATIO = (BTN_3DOTS_X - _BASELINE_X) / _BASELINE_W
BTN_3DOTS_Y_RATIO = (BTN_3DOTS_Y - _BASELINE_Y) / _BASELINE_H
BTN_COPY_LINK_X_RATIO = (BTN_COPY_LINK_X - _BASELINE_X) / _BASELINE_W
BTN_COPY_LINK_Y_RATIOS = [
    (value - _BASELINE_Y) / _BASELINE_H for value in BTN_COPY_LINK_Y_CANDIDATES
]

# Import window manager
try:
    from wechat_favorites_exporter.window_manager import (
        activate_wechat,
        close_front_window,
        get_front_window_bounds,
        get_wechat_window_count,
    )
except ImportError:
    print("WARNING: window_manager not found, using fallback")
    def activate_wechat() -> None:
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
    def get_front_window_bounds() -> Optional[tuple[int, int, int, int]]:
        return None
    def get_wechat_window_count() -> int:
        return 1
    def close_front_window() -> None:
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.3)


def close_detail_window():
    """Close the detail view / built-in browser window"""
    pyautogui.press('esc')
    time.sleep(0.5)
    if get_wechat_window_count() > 1:
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.5)


def ensure_single_wechat_window(max_attempts: int = 5) -> None:
    """Close extra WeChat windows so the script always starts from one stable window."""
    attempts = 0
    while get_wechat_window_count() > 1 and attempts < max_attempts:
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.8)
        attempts += 1
    activate_wechat()
    time.sleep(0.5)


def get_relative_point(bounds: tuple[int, int, int, int], x_ratio: float, y_ratio: float) -> tuple[int, int]:
    x, y, width, height = bounds
    return round(x + width * x_ratio), round(y + height * y_ratio)


def get_list_area_point(bounds: tuple[int, int, int, int]) -> tuple[int, int]:
    return get_relative_point(bounds, LIST_AREA_X_RATIO, LIST_AREA_Y_RATIO)


def get_card_point(bounds: tuple[int, int, int, int], local_idx: int) -> tuple[int, int]:
    card_x, card_y = get_relative_point(bounds, FIRST_ITEM_X_RATIO, FIRST_ITEM_Y_RATIO)
    item_height = round(bounds[3] * ITEM_HEIGHT_RATIO)
    return card_x, card_y + (local_idx * item_height)


def get_three_dots_point(bounds: tuple[int, int, int, int]) -> tuple[int, int]:
    return get_relative_point(bounds, BTN_3DOTS_X_RATIO, BTN_3DOTS_Y_RATIO)


def get_copy_link_points(bounds: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    return [
        get_relative_point(bounds, BTN_COPY_LINK_X_RATIO, y_ratio)
        for y_ratio in BTN_COPY_LINK_Y_RATIOS
    ]


def get_clipboard_url() -> str | None:
    content = (pyperclip.paste() or '').strip()
    return content if content.startswith('http') else None


def export_card(global_idx: int, card_x: int, card_y: int) -> Optional[str]:
    """Export a single favorite card. Returns the extracted link or None."""
    
    ensure_single_wechat_window()
    activate_wechat()
    time.sleep(0.3)

    # Clear clipboard to ensure we catch the new URL
    pyperclip.copy('')

    # Click to open the card
    pyautogui.click(card_x, card_y)
    # Increase wait time to ensure content is fully loaded
    time.sleep(2.5)

    bounds = get_front_window_bounds()
    if not bounds:
        print(f'  [{global_idx:03d}] Window lost')
        return None

    extracted_url: Optional[str] = None
    try:
        dots_x, dots_y = get_three_dots_point(bounds)
        copy_link_points = get_copy_link_points(bounds)

        for idx, (copy_x, copy_y) in enumerate(copy_link_points):
            pyperclip.copy('')

            # Click "..."
            pyautogui.click(dots_x, dots_y)
            time.sleep(3.0)

            # Click candidate "复制链接"
            pyautogui.click(copy_x, copy_y)
            time.sleep(3.0)

            extracted_url = get_clipboard_url()
            if extracted_url:
                break

            # Candidate missed. Close current menu state before retrying.
            if idx < len(BTN_COPY_LINK_Y_CANDIDATES) - 1:
                pyautogui.press('esc')
                time.sleep(0.5)
            
    except Exception as e:
        print(f'  [Menu error: {e}]')
        return None

    # Close menu
    pyautogui.press('esc')
    time.sleep(0.2)

    # Close detail
    pyautogui.press('esc')
    time.sleep(0.5)
    close_detail_window()
    time.sleep(0.5)
    ensure_single_wechat_window()
    
    return extracted_url


def main():
    max_items = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Link output file
    LINKS_FILE = "wechat_links.txt"
    saved_links = []
    
    # Based on measurement: User requested exact scroll distance: 890px
    SCROLL_DISTANCE_PX = 890
    # 轻微上调，逼近实测一屏高度，减少 local3 的残留重叠。
    SCROLL_CLICKS = 54 
    SCROLL_STEP = 18
    # Real validation shows page 2 overlaps first 3 visible items.
    PAGE_OVERLAP_ITEMS = 3

    # Activate WeChat and go to 全部收藏
    activate_wechat()
    time.sleep(0.5)
    ensure_single_wechat_window()

    bounds = get_front_window_bounds()
    if bounds:
        list_x, list_y = get_list_area_point(bounds)
        pyautogui.click(list_x, list_y)
        time.sleep(0.5)

    # Scroll to top first
    if bounds:
        wx, wy, ww, wh = bounds
        # Keep the original top-reset behavior stable for page 1.
        scroll_x = wx + int(ww * 0.7)
        scroll_y = wy + 200
        
        pyautogui.moveTo(scroll_x, scroll_y)
        for _ in range(50):
            pyautogui.scroll(20)
            time.sleep(0.02)
        time.sleep(0.5)

    print(f"Extracting links for up to {max_items} items...")
    print(f"Will save to: {os.path.abspath(LINKS_FILE)}\n")
    print(f"Card: X={FIRST_ITEM_X}, Y={FIRST_ITEM_Y}, Height={ITEM_HEIGHT}")
    print(f"Items per page: {ITEMS_PER_PAGE}")
    print(f"Scroll strategy: {SCROLL_DISTANCE_PX}px per page via {SCROLL_CLICKS} clicks\n")

    global_idx = 0
    page = 0
    seen_urls = set() # For faster duplicate checking

    while global_idx < max_items:
        start_local_idx = 0 if page == 0 else PAGE_OVERLAP_ITEMS
        items_this_page = min(ITEMS_PER_PAGE - start_local_idx, max_items - global_idx)
        
        # Page-start focus recovery:
        # Do NOT click "全部收藏" again after page 1, or the right-side list may reset
        # to the top and cause duplicate extraction on page 2+.
        print(f">>> Starting Page {page + 1}: Waking up focus...")
        activate_wechat()
        time.sleep(0.5)
        page_bounds = get_front_window_bounds()
        if not page_bounds:
            print("[NO WINDOW]")
            break

        if page == 0:
            list_x, list_y = get_list_area_point(page_bounds)
            pyautogui.click(list_x, list_y)
            time.sleep(0.5)
        else:
            card_x, card_y = get_card_point(page_bounds, 0)
            pyautogui.moveTo(card_x - 60, card_y)
            time.sleep(0.5)

        for local_idx in range(start_local_idx, start_local_idx + items_this_page):
            current_bounds = get_front_window_bounds()
            if not current_bounds:
                print("[NO WINDOW]")
                break
            card_x, card_y = get_card_point(current_bounds, local_idx)
            print(f'Item {global_idx} (local {local_idx}, Y={card_y}):', end=' ')
            
            url = export_card(global_idx, card_x, card_y)
            
            if url:
                if url not in seen_urls:
                    seen_urls.add(url)
                    saved_links.append(url)
                    with open(LINKS_FILE, 'a', encoding='utf-8') as f:
                        f.write(url + '\n')
                    print(f"[LINK] {url[:30]}...")
                else:
                    print("[SKIP] Duplicate")
            else:
                print("[NO LINK]")
                
            global_idx += 1
            if global_idx >= max_items:
                break
        
        # Scroll down to next page
        if global_idx < max_items:
            bounds = get_front_window_bounds()
            if bounds:
                wx, wy, ww, wh = bounds
                card_x, card_y = get_card_point(bounds, 3)
                scroll_x = card_x
                scroll_y = card_y
                
                print(f'\n--- Scrolling to page {page + 2} (890px) ---')
                pyautogui.moveTo(scroll_x, scroll_y)
                time.sleep(0.3)
                
                # Execute scroll (890px)
                for _ in range(SCROLL_CLICKS):
                    pyautogui.scroll(-SCROLL_STEP)
                    time.sleep(0.02)
                
                # Keep the scrolled position intact and only wake up hover/render state.
                print("[Hovering to trigger lazy load & waiting 3s for render...]")
                next_card_x, next_card_y = get_card_point(bounds, 0)
                pyautogui.moveTo(next_card_x - 50, next_card_y) # Hover near the list
                time.sleep(3.5) # Wait for WeChat to render new images/DOM
            else:
                print('\n[WARN] Lost window bounds, stopping')
                break
            
            page += 1
    
    print(f'\n=== Done: {global_idx} items checked ===')
    print(f'Total unique links saved: {len(saved_links)}')
    print(f'File: {os.path.abspath(LINKS_FILE)}')


if __name__ == "__main__":
    main()
