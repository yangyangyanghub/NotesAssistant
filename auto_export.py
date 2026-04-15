#!/usr/bin/env python3
"""
Auto-export WeChat favorites (Windows version).
Strategy: Process visible cards one by one, then scroll down for next page.
"""
import json
import os
import platform
import sys
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

import pyautogui
import pyperclip

# === Platform Detection ===r_engine = None

# === Platform Detection ===
_IS_MACOS = platform.system() == "Darwin"
_IS_WINDOWS = platform.system() == "Windows"
_MODIFIER_KEY = "command" if _IS_MACOS else "ctrl"

# === Config ===
OUTPUT_DIR = "output/全部收藏"
FIRST_ITEM_X = 1040      # X coordinate for clicking cards
FIRST_ITEM_Y = 158       # Y coordinate of first visible card
ITEM_HEIGHT = 130        # Vertical distance between adjacent cards
ITEMS_PER_PAGE = 7       # Cards visible per screen
LIST_AREA_X = 151        # X of "全部收藏" category tab
LIST_AREA_Y = 153        # Y of "全部收藏" category tab

# Menu coordinates (relative to window's top-right corner)
# Based on measurements: 3 dots at (1803, 23), Copy Link at (1683, 241)
MENU_3DOTS_OFFSET_X = 133  # From right edge (WindowWidth - 133)
MENU_3DOTS_OFFSET_Y = 31   # From top edge
MENU_COPY_LINK_OFFSET_X = 253  # From right edge
MENU_COPY_LINK_OFFSET_Y = 249  # From top edge

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
    def activate_wechat():
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
    def get_front_window_bounds():
        return None
    def get_wechat_window_count():
        return 1
    def close_front_window():
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.3)


def close_detail_window():
    """Close the detail view / built-in browser window"""
    pyautogui.press('esc')
    time.sleep(0.5)
    if get_wechat_window_count() > 1:
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.5)


def export_card(global_idx: int, card_y: int) -> str:
    """Export a single favorite card. Returns the extracted link or None."""
    
    activate_wechat()
    time.sleep(0.3)

    # Clear clipboard to ensure we catch the new URL
    pyperclip.copy('')

    # Click to open the card
    pyautogui.click(FIRST_ITEM_X, card_y)
    # Increase wait time to ensure content is fully loaded
    time.sleep(2.5)

    bounds = get_front_window_bounds()
    if not bounds:
        print(f'  [{global_idx:03d}] Window lost')
        return None

    wx, wy, ww, wh = bounds
    
    extracted_url = ""
    try:
        # Calculate menu positions based on current window bounds
        dots_x = wx + ww - MENU_3DOTS_OFFSET_X
        dots_y = wy + MENU_3DOTS_OFFSET_Y
        link_x = wx + ww - MENU_COPY_LINK_OFFSET_X
        link_y = wy + MENU_COPY_LINK_OFFSET_Y

        # Click "..."
        pyautogui.click(dots_x, dots_y)
        time.sleep(3.0)
        
        # Click "Copy Link"
        pyautogui.click(link_x, link_y)
        time.sleep(3.0)
        
        # Get URL from clipboard
        # Check twice to be safe against race conditions
        extracted_url = (pyperclip.paste() or '').strip()
        if not extracted_url.startswith('http'):
            time.sleep(1.0)
            extracted_url = (pyperclip.paste() or '').strip()
            if not extracted_url.startswith('http'):
                extracted_url = None
            
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
    
    return extracted_url


def main():
    max_items = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Link output file
    LINKS_FILE = "wechat_links.txt"
    saved_links = []
    
    # Based on measurement: User requested exact scroll distance: 890px
    SCROLL_DISTANCE_PX = 890
    # 890px / 18px per scroll ≈ 50 clicks.
    SCROLL_CLICKS = 50 
    SCROLL_STEP = 18

    # Activate WeChat and go to 全部收藏
    activate_wechat()
    time.sleep(0.5)
    pyautogui.click(LIST_AREA_X, LIST_AREA_Y)
    time.sleep(0.5)

    # Scroll to top first
    bounds = get_front_window_bounds()
    if bounds:
        wx, wy, ww, wh = bounds
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
        items_this_page = min(ITEMS_PER_PAGE, max_items - global_idx)
        
        # CRITICAL FIX for Page 2+ Failure:
        # Before starting a new page, explicitly activate WeChat and hover to wake up the DOM.
        # WeChat often goes "sleep" or loses focus after a scroll event.
        print(f">>> Starting Page {page + 1}: Waking up focus...")
        activate_wechat()
        time.sleep(0.5)
        pyautogui.click(LIST_AREA_X, LIST_AREA_Y) # Click sidebar to ensure list view is active
        time.sleep(0.5)

        for local_idx in range(items_this_page):
            card_y = FIRST_ITEM_Y + (local_idx * ITEM_HEIGHT)
            print(f'Item {global_idx} (local {local_idx}, Y={card_y}):', end=' ')
            
            url = export_card(global_idx, card_y)
            
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
                scroll_x = wx + int(ww * 0.7)
                scroll_y = wy + int(wh * 0.5)
                
                print(f'\n--- Scrolling to page {page + 2} (890px) ---')
                pyautogui.moveTo(scroll_x, scroll_y)
                time.sleep(0.3)
                
                # Execute scroll (890px)
                for _ in range(SCROLL_CLICKS):
                    pyautogui.scroll(-SCROLL_STEP)
                    time.sleep(0.02)
                
                # CRITICAL FIX: Wake Up Mechanism for new items
                # 1. Move mouse to the header area to ensure we haven't scrolled past the list
                # 2. Hover over the list to trigger lazy load of new cards
                print("[Hovering to trigger lazy load & waiting 3s for render...]")
                pyautogui.moveTo(FIRST_ITEM_X - 50, FIRST_ITEM_Y) # Hover near the list
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
