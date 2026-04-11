# WeChat Favorites Exporter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pyautogui + AppleScript macOS tool that batch-exports WeChat favorites (screenshots + text + metadata) with category-based processing and resume support.

**Architecture:** Six modules — config (constants + helpers), window_manager (AppleScript bridge), calibrator (coordinate capture), content_extractor (screenshots + text + OCR), exporter (main loop), main (CLI entry). TDD with pytest; UI-dependent code wrapped behind interfaces for testability.

**Tech Stack:** Python 3.12, pyautogui, Pillow, pyperclip, pytesseract, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `wechat_favorites_exporter/config.py` | Constants, random_delay(), progress/calibration JSON I/O |
| `wechat_favorites_exporter/window_manager.py` | AppleScript calls: window count, bounds, close, activate |
| `wechat_favorites_exporter/calibrator.py` | Interactive coordinate calibration, save/load calibration.json |
| `wechat_favorites_exporter/content_extractor.py` | Screenshot, long screenshot, OCR preview, text extraction, image hash, URL extraction |
| `wechat_favorites_exporter/exporter.py` | Main export loop, should_skip, resume logic |
| `wechat_favorites_exporter/main.py` | argparse CLI entry point |
| `wechat_favorites_exporter/__init__.py` | Package marker |
| `tests/__init__.py` | Test package marker |
| `tests/test_config.py` | Tests for config module |
| `tests/test_content_extractor.py` | Tests for content_extractor (pure functions) |
| `tests/test_window_manager.py` | Tests for window_manager (mocked subprocess) |
| `tests/test_exporter.py` | Tests for exporter logic (mocked UI) |
| `tests/test_calibrator.py` | Tests for calibrator I/O |
| `requirements.txt` | Dependencies |

---

### Task 1: Project scaffolding and config module

**Files:**
- Create: `wechat_favorites_exporter/__init__.py`
- Create: `wechat_favorites_exporter/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
pyautogui
Pillow
pyperclip
pytesseract
pytest
```

- [ ] **Step 2: Install dependencies**

Run: `pip install pyautogui pyperclip pytesseract pytest`
Expected: Successfully installed

- [ ] **Step 3: Create package markers**

Create `wechat_favorites_exporter/__init__.py` (empty file).
Create `tests/__init__.py` (empty file).

- [ ] **Step 4: Write failing tests for config**

```python
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
    """random_delay should sleep between CLICK_DELAY_MIN and some reasonable max."""
    delays = []
    with patch("time.sleep", side_effect=lambda d: delays.append(d)):
        for _ in range(100):
            random_delay()
    assert all(d >= CLICK_DELAY_MIN for d in delays)
    assert all(d < 10 for d in delays)
    # Should have variance (not all the same)
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
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `cd /Users/linux/Documents/NotesAssistant && python -m pytest tests/test_config.py -v`
Expected: FAIL — ModuleNotFoundError: No module named 'wechat_favorites_exporter'

- [ ] **Step 6: Implement config.py**

```python
# wechat_favorites_exporter/config.py
import json
import os
import random
import time

# Constants
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
    """Normal-distribution random delay to mimic human pace."""
    delay = max(CLICK_DELAY_MIN, random.gauss(CLICK_DELAY_MEAN, CLICK_DELAY_STD))
    time.sleep(delay)


def save_progress(data: dict, path: str) -> None:
    """Save progress dict to JSON file."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_progress(path: str) -> dict | None:
    """Load progress from JSON file. Returns None if file missing."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/linux/Documents/NotesAssistant && python -m pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 8: Commit**

```bash
git add wechat_favorites_exporter/ tests/ requirements.txt
git commit -m "feat: add config module with constants, random_delay, progress I/O"
```

---

### Task 2: Window manager module

**Files:**
- Create: `wechat_favorites_exporter/window_manager.py`
- Create: `tests/test_window_manager.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_window_manager.py
from unittest.mock import patch, MagicMock
import subprocess

from wechat_favorites_exporter.window_manager import (
    get_wechat_window_count,
    get_front_window_bounds,
    close_front_window,
    activate_wechat,
    wait_for_new_window,
)


def test_get_wechat_window_count():
    mock_result = MagicMock()
    mock_result.stdout = "3\n"
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        count = get_wechat_window_count()
        assert count == 3
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "osascript" in call_args[0][0]


def test_get_front_window_bounds():
    mock_result = MagicMock()
    mock_result.stdout = "100, 200, 800, 600\n"
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result):
        bounds = get_front_window_bounds()
        assert bounds == (100, 200, 800, 600)


def test_get_front_window_bounds_error():
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 1
    with patch("subprocess.run", return_value=mock_result):
        bounds = get_front_window_bounds()
        assert bounds is None


def test_close_front_window():
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        close_front_window()
        mock_run.assert_called_once()


def test_activate_wechat():
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        activate_wechat()
        mock_run.assert_called_once()


def test_wait_for_new_window_success():
    """Should return True when window count increases."""
    counts = [2, 2, 3]  # Third poll shows new window
    mock_results = [MagicMock(stdout=f"{c}\n", returncode=0) for c in counts]
    with patch("subprocess.run", side_effect=mock_results):
        with patch("time.sleep"):
            result = wait_for_new_window(2, timeout=5.0)
            assert result is True


def test_wait_for_new_window_timeout():
    """Should return False when timeout and no new window."""
    mock_result = MagicMock(stdout="2\n", returncode=0)
    with patch("subprocess.run", return_value=mock_result):
        with patch("time.sleep"):
            with patch("time.time", side_effect=[0, 0.5, 1.0, 5.1]):
                result = wait_for_new_window(2, timeout=5.0)
                assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_window_manager.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement window_manager.py**

```python
# wechat_favorites_exporter/window_manager.py
import subprocess
import time


def _run_applescript(script: str) -> subprocess.CompletedProcess:
    """Run an AppleScript and return the result."""
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10,
    )


def get_wechat_window_count() -> int:
    """Get the number of WeChat windows currently open."""
    script = '''
    tell application "System Events"
        tell process "WeChat"
            return count of windows
        end tell
    end tell
    '''
    result = _run_applescript(script)
    try:
        return int(result.stdout.strip())
    except (ValueError, AttributeError):
        return 0


def get_front_window_bounds() -> tuple[int, int, int, int] | None:
    """Get (x, y, width, height) of the frontmost WeChat window."""
    script = '''
    tell application "System Events"
        tell process "WeChat"
            set winPos to position of front window
            set winSize to size of front window
            return (item 1 of winPos) & ", " & (item 2 of winPos) & ", " & (item 1 of winSize) & ", " & (item 2 of winSize)
        end tell
    end tell
    '''
    result = _run_applescript(script)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        parts = [int(x.strip()) for x in result.stdout.strip().split(",")]
        return (parts[0], parts[1], parts[2], parts[3])
    except (ValueError, IndexError):
        return None


def close_front_window() -> None:
    """Close the frontmost WeChat window using Cmd+W."""
    script = '''
    tell application "System Events"
        tell process "WeChat"
            keystroke "w" using command down
        end tell
    end tell
    '''
    _run_applescript(script)


def activate_wechat() -> None:
    """Bring WeChat to the foreground."""
    script = 'tell application "WeChat" to activate'
    _run_applescript(script)


def wait_for_new_window(original_count: int, timeout: float = 5.0) -> bool:
    """Poll until WeChat has more windows than original_count. Returns True on success."""
    start = time.time()
    while time.time() - start < timeout:
        current = get_wechat_window_count()
        if current > original_count:
            return True
        time.sleep(0.3)
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_window_manager.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add wechat_favorites_exporter/window_manager.py tests/test_window_manager.py
git commit -m "feat: add window_manager module with AppleScript bridge"
```

---

### Task 3: Content extractor — pure functions

**Files:**
- Create: `wechat_favorites_exporter/content_extractor.py`
- Create: `tests/test_content_extractor.py`
- Create: `tests/fixtures/` (test images)

- [ ] **Step 1: Write failing tests for pure functions**

```python
# tests/test_content_extractor.py
from PIL import Image
from wechat_favorites_exporter.content_extractor import (
    extract_urls,
    compute_image_hash,
    images_are_similar,
    is_preview_sufficient,
    stitch_screenshots,
)


def test_extract_urls_finds_http():
    text = "Visit https://example.com/path and http://foo.bar/baz for more"
    urls = extract_urls(text)
    assert "https://example.com/path" in urls
    assert "http://foo.bar/baz" in urls


def test_extract_urls_no_urls():
    assert extract_urls("no urls here") == []


def test_extract_urls_chinese_mixed():
    text = "管理后台地址：https://e-tmh.qcode.cc/admin-next/api 详情见此"
    urls = extract_urls(text)
    assert "https://e-tmh.qcode.cc/admin-next/api" in urls


def test_compute_image_hash_deterministic():
    img = Image.new("RGB", (100, 100), color="red")
    h1 = compute_image_hash(img)
    h2 = compute_image_hash(img)
    assert h1 == h2
    assert len(h1) == 16  # 64-bit hash as hex


def test_compute_image_hash_different_images():
    red = Image.new("RGB", (100, 100), color="red")
    blue = Image.new("RGB", (100, 100), color="blue")
    assert compute_image_hash(red) != compute_image_hash(blue)


def test_images_are_similar_identical():
    img = Image.new("RGB", (100, 100), color="red")
    assert images_are_similar(img, img, threshold=5) is True


def test_images_are_similar_different():
    red = Image.new("RGB", (100, 100), color="red")
    blue = Image.new("RGB", (100, 100), color="blue")
    assert images_are_similar(red, blue, threshold=5) is False


def test_is_preview_sufficient_text_note():
    preview = {"title": "密码是1234", "source": "撕考者", "date": "3月5日", "type_hint": ""}
    assert is_preview_sufficient(preview) is True


def test_is_preview_sufficient_link():
    preview = {"title": "Some article", "source": "someone", "date": "3月5日", "type_hint": "链接"}
    assert is_preview_sufficient(preview) is False


def test_is_preview_sufficient_file():
    preview = {"title": "Guide", "source": "x", "date": "3月4日", "type_hint": "DOCX 29.0KB"}
    assert is_preview_sufficient(preview) is False


def test_stitch_screenshots_single():
    img = Image.new("RGB", (400, 300), color="white")
    result = stitch_screenshots([img])
    assert result.size == (400, 300)


def test_stitch_screenshots_multiple():
    img1 = Image.new("RGB", (400, 300), color="red")
    img2 = Image.new("RGB", (400, 300), color="blue")
    result = stitch_screenshots([img1, img2], overlap=60)
    # Height = 300 + 300 - 60 = 540
    assert result.size == (400, 540)


def test_stitch_screenshots_overlap_crops_correctly():
    img1 = Image.new("RGB", (200, 100), color="red")
    img2 = Image.new("RGB", (200, 100), color="blue")
    result = stitch_screenshots([img1, img2], overlap=20)
    # Top should be red, bottom should be blue
    assert result.getpixel((100, 10)) == (255, 0, 0)  # red area
    assert result.getpixel((100, 170)) == (0, 0, 255)  # blue area
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_content_extractor.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement content_extractor.py (pure functions)**

```python
# wechat_favorites_exporter/content_extractor.py
import re
import subprocess

from PIL import Image


def extract_urls(text: str) -> list[str]:
    """Extract HTTP/HTTPS URLs from text."""
    pattern = r'https?://[^\s<>"\'\]）》，。、\u4e00-\u9fff]+'
    return re.findall(pattern, text)


def compute_image_hash(image: Image.Image) -> str:
    """Compute a perceptual average hash (64-bit) for dedup."""
    small = image.resize((8, 8)).convert("L")
    pixels = list(small.getdata())
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p > avg else "0" for p in pixels)
    return f"{int(bits, 2):016x}"


def images_are_similar(img1: Image.Image, img2: Image.Image, threshold: int = 5) -> bool:
    """Compare two images by hamming distance of their perceptual hashes."""
    h1 = compute_image_hash(img1)
    h2 = compute_image_hash(img2)
    diff = bin(int(h1, 16) ^ int(h2, 16)).count("1")
    return diff <= threshold


def is_preview_sufficient(preview: dict) -> bool:
    """Check if the list preview has enough info to skip opening detail."""
    type_hint = preview.get("type_hint", "").strip()
    # If there's a type hint indicating file/link/media, need to open detail
    skip_hints = ["DOCX", "PDF", "XLSX", "PPT", "链接", "KB", "MB", "http"]
    if any(h in type_hint for h in skip_hints):
        return False
    title = preview.get("title", "")
    # Short plain text with no link indicators — preview is enough
    if title and len(title) < 200 and "http" not in title:
        return True
    return False


def stitch_screenshots(images: list[Image.Image], overlap: int = 0) -> Image.Image:
    """Vertically stitch screenshots, cropping overlap from subsequent images."""
    if len(images) == 1:
        return images[0]
    width = images[0].width
    total_height = images[0].height + sum(img.height - overlap for img in images[1:])
    result = Image.new("RGB", (width, total_height))
    y = 0
    for i, img in enumerate(images):
        if i == 0:
            result.paste(img, (0, 0))
            y = img.height
        else:
            cropped = img.crop((0, overlap, img.width, img.height))
            result.paste(cropped, (0, y))
            y += cropped.height
    return result


def capture_window_screenshot(bounds: tuple[int, int, int, int]) -> Image.Image:
    """Capture a screenshot of the specified region (x, y, w, h)."""
    from PIL import ImageGrab
    x, y, w, h = bounds
    bbox = (x, y, x + w, y + h)
    return ImageGrab.grab(bbox=bbox)


def extract_text_from_clipboard() -> str | None:
    """Read the current macOS clipboard content."""
    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        return result.stdout if result.stdout else None
    except Exception:
        return None


def ocr_extract_preview(image: Image.Image) -> dict:
    """OCR extract preview info from a list item screenshot."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
    except Exception:
        text = ""

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    title = lines[0] if lines else ""
    source = ""
    date = ""
    type_hint = ""

    for line in lines[1:]:
        # Look for date patterns like "3月4日", "星期四"
        if re.search(r'\d+月\d+日|星期', line):
            date = line
        elif re.search(r'(DOCX|PDF|XLSX|PPT|KB|MB)', line, re.IGNORECASE):
            type_hint = line
        elif not source:
            source = line

    return {"title": title, "source": source, "date": date, "type_hint": type_hint}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_content_extractor.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add wechat_favorites_exporter/content_extractor.py tests/test_content_extractor.py
git commit -m "feat: add content_extractor with URL extraction, image hash, stitching, OCR"
```

---

### Task 4: Calibrator module

**Files:**
- Create: `wechat_favorites_exporter/calibrator.py`
- Create: `tests/test_calibrator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_calibrator.py
import json
from wechat_favorites_exporter.calibrator import (
    CalibrationData,
    save_calibration,
    load_calibration,
    compute_category_position,
)


def test_calibration_data_creation():
    data = CalibrationData(
        category_start_pos=(100, 200),
        first_item_pos=(550, 150),
        list_bottom_pos=(550, 700),
        visible_count=5,
        category_spacing=56,
    )
    assert data.list_area_height == 550  # 700 - 150
    assert data.scroll_amount == 440  # 550 * 0.8
    assert data.click_x == 550
    assert data.click_y == 150


def test_save_and_load_calibration(tmp_path):
    path = str(tmp_path / "cal.json")
    data = CalibrationData(
        category_start_pos=(100, 200),
        first_item_pos=(550, 150),
        list_bottom_pos=(550, 700),
        visible_count=5,
        category_spacing=56,
    )
    save_calibration(data, path)
    loaded = load_calibration(path)
    assert loaded.category_start_pos == (100, 200)
    assert loaded.first_item_pos == (550, 150)
    assert loaded.visible_count == 5


def test_load_calibration_missing(tmp_path):
    path = str(tmp_path / "missing.json")
    assert load_calibration(path) is None


def test_compute_category_position():
    data = CalibrationData(
        category_start_pos=(100, 200),
        first_item_pos=(550, 150),
        list_bottom_pos=(550, 700),
        visible_count=5,
        category_spacing=56,
    )
    # "链接" is index 2 in CATEGORIES
    x, y = compute_category_position(data, "链接")
    assert x == 100
    assert y == 200 + 2 * 56  # 312


def test_compute_category_position_unknown():
    data = CalibrationData(
        category_start_pos=(100, 200),
        first_item_pos=(550, 150),
        list_bottom_pos=(550, 700),
        visible_count=5,
        category_spacing=56,
    )
    result = compute_category_position(data, "不存在的分类")
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_calibrator.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement calibrator.py**

```python
# wechat_favorites_exporter/calibrator.py
import json
import os
from dataclasses import dataclass

from wechat_favorites_exporter.config import CATEGORIES


@dataclass
class CalibrationData:
    category_start_pos: tuple[int, int]
    first_item_pos: tuple[int, int]
    list_bottom_pos: tuple[int, int]
    visible_count: int
    category_spacing: int = 56

    @property
    def list_area_height(self) -> int:
        return self.list_bottom_pos[1] - self.first_item_pos[1]

    @property
    def scroll_amount(self) -> int:
        return int(self.list_area_height * 0.8)

    @property
    def click_x(self) -> int:
        return self.first_item_pos[0]

    @property
    def click_y(self) -> int:
        return self.first_item_pos[1]


def save_calibration(data: CalibrationData, path: str) -> None:
    """Save calibration data to JSON."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    obj = {
        "category_start_pos": list(data.category_start_pos),
        "first_item_pos": list(data.first_item_pos),
        "list_bottom_pos": list(data.list_bottom_pos),
        "visible_count": data.visible_count,
        "category_spacing": data.category_spacing,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def load_calibration(path: str) -> CalibrationData | None:
    """Load calibration data from JSON. Returns None if file missing."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return CalibrationData(
        category_start_pos=tuple(obj["category_start_pos"]),
        first_item_pos=tuple(obj["first_item_pos"]),
        list_bottom_pos=tuple(obj["list_bottom_pos"]),
        visible_count=obj["visible_count"],
        category_spacing=obj.get("category_spacing", 56),
    )


def compute_category_position(data: CalibrationData, category: str) -> tuple[int, int] | None:
    """Compute click position for a category in the left sidebar."""
    if category not in CATEGORIES:
        return None
    index = CATEGORIES.index(category)
    x = data.category_start_pos[0]
    y = data.category_start_pos[1] + index * data.category_spacing
    return (x, y)


def run_calibration() -> CalibrationData:
    """Interactive calibration: prompt user to move mouse to key positions."""
    import pyautogui

    print("\n=== 坐标校准 ===")
    print("请确保微信收藏夹页面已打开\n")

    input("步骤 1/4：请把鼠标移到左侧「全部收藏」的位置，然后按 Enter...")
    category_start_pos = pyautogui.position()
    print(f"  记录: {category_start_pos}")

    input("步骤 2/4：请把鼠标移到右侧列表第一条收藏的中心，然后按 Enter...")
    first_item_pos = pyautogui.position()
    print(f"  记录: {first_item_pos}")

    input("步骤 3/4：请把鼠标移到右侧列表可见区域的底部边缘，然后按 Enter...")
    list_bottom_pos = pyautogui.position()
    print(f"  记录: {list_bottom_pos}")

    visible_count = int(input("步骤 4/4：当前可见几条收藏？请输入数字: "))

    data = CalibrationData(
        category_start_pos=(category_start_pos.x, category_start_pos.y),
        first_item_pos=(first_item_pos.x, first_item_pos.y),
        list_bottom_pos=(list_bottom_pos.x, list_bottom_pos.y),
        visible_count=visible_count,
    )
    print(f"\n校准完成！列表区域高度: {data.list_area_height}px, 每次滚动: {data.scroll_amount}px")
    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_calibrator.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add wechat_favorites_exporter/calibrator.py tests/test_calibrator.py
git commit -m "feat: add calibrator with CalibrationData, save/load, category position"
```

---

### Task 5: Exporter — should_skip and resume logic

**Files:**
- Create: `wechat_favorites_exporter/exporter.py`
- Create: `tests/test_exporter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_exporter.py
import json
import os

from wechat_favorites_exporter.exporter import should_skip, save_item_meta, create_item_dir


def test_should_skip_no_dir(tmp_path):
    preview = {"title": "test", "date": "3月5日"}
    assert should_skip(1, preview, str(tmp_path)) is False


def test_should_skip_no_meta(tmp_path):
    item_dir = tmp_path / "001"
    item_dir.mkdir()
    preview = {"title": "test", "date": "3月5日"}
    assert should_skip(1, preview, str(tmp_path)) is False


def test_should_skip_matching_meta(tmp_path):
    item_dir = tmp_path / "001"
    item_dir.mkdir()
    meta = {
        "index": 1,
        "preview": {"title": "密码是1234", "date": "3月5日"},
    }
    with open(item_dir / "meta.json", "w") as f:
        json.dump(meta, f)
    preview = {"title": "密码是1234", "date": "3月5日"}
    assert should_skip(1, preview, str(tmp_path)) is True


def test_should_skip_mismatched_meta(tmp_path):
    item_dir = tmp_path / "001"
    item_dir.mkdir()
    meta = {
        "index": 1,
        "preview": {"title": "other title", "date": "3月5日"},
    }
    with open(item_dir / "meta.json", "w") as f:
        json.dump(meta, f)
    preview = {"title": "密码是1234", "date": "3月5日"}
    assert should_skip(1, preview, str(tmp_path)) is False


def test_create_item_dir(tmp_path):
    path = create_item_dir(str(tmp_path), 42)
    assert os.path.isdir(path)
    assert path.endswith("042")


def test_save_item_meta(tmp_path):
    item_dir = tmp_path / "001"
    item_dir.mkdir()
    meta = {"index": 1, "category": "链接", "preview": {"title": "test"}}
    save_item_meta(str(item_dir), meta)
    loaded = json.load(open(item_dir / "meta.json"))
    assert loaded["index"] == 1
    assert loaded["preview"]["title"] == "test"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_exporter.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement exporter.py (data functions only)**

```python
# wechat_favorites_exporter/exporter.py
import json
import os
from datetime import datetime


def should_skip(index: int, preview: dict, output_dir: str) -> bool:
    """Check if this item was already exported by comparing preview title+date."""
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
    """Create and return the directory for item N (e.g., output/042/)."""
    item_dir = os.path.join(output_dir, f"{index:03d}")
    os.makedirs(item_dir, exist_ok=True)
    return item_dir


def save_item_meta(item_dir: str, meta: dict) -> None:
    """Save meta.json to the item directory."""
    path = os.path.join(item_dir, "meta.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def build_meta(
    index: int,
    category: str,
    preview: dict,
    text: str | None = None,
    urls: list[str] | None = None,
    image_hash: str = "",
    open_failed: bool = False,
    skipped_detail: bool = False,
    screenshot_pages: int = 1,
    error: str | None = None,
) -> dict:
    """Build a meta.json dict for one item."""
    return {
        "index": index,
        "category": category,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "has_text": text is not None and len(text) > 0,
        "urls": urls or [],
        "open_failed": open_failed,
        "skipped_detail": skipped_detail,
        "preview": preview,
        "error": error,
        "image_hash": image_hash,
        "screenshot_pages": screenshot_pages,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_exporter.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add wechat_favorites_exporter/exporter.py tests/test_exporter.py
git commit -m "feat: add exporter with should_skip, save_item_meta, build_meta"
```

---

### Task 6: Exporter — main export loop

**Files:**
- Modify: `wechat_favorites_exporter/exporter.py`
- Modify: `tests/test_exporter.py`

- [ ] **Step 1: Write failing test for export_one_item**

```python
# append to tests/test_exporter.py
from unittest.mock import patch, MagicMock, call
from PIL import Image

from wechat_favorites_exporter.exporter import export_one_item
from wechat_favorites_exporter.calibrator import CalibrationData


def _make_cal_data():
    return CalibrationData(
        category_start_pos=(100, 200),
        first_item_pos=(550, 150),
        list_bottom_pos=(550, 700),
        visible_count=5,
    )


@patch("wechat_favorites_exporter.exporter.window_manager")
@patch("wechat_favorites_exporter.exporter.content_extractor")
@patch("wechat_favorites_exporter.exporter.pyautogui")
def test_export_one_item_normal(mock_pyautogui, mock_extractor, mock_wm, tmp_path):
    """Test normal flow: click item, window opens, screenshot, extract text, close."""
    cal = _make_cal_data()
    test_img = Image.new("RGB", (800, 600), color="white")

    # Setup mocks
    mock_wm.get_wechat_window_count.return_value = 1
    mock_wm.wait_for_new_window.return_value = True
    mock_wm.get_front_window_bounds.return_value = (100, 100, 800, 600)

    mock_extractor.ocr_extract_preview.return_value = {
        "title": "Test Article", "source": "test", "date": "3月5日", "type_hint": "链接"
    }
    mock_extractor.is_preview_sufficient.return_value = False
    mock_extractor.capture_window_screenshot.return_value = test_img
    mock_extractor.images_are_similar.return_value = False
    mock_extractor.extract_text_from_clipboard.return_value = "some text https://example.com"
    mock_extractor.extract_urls.return_value = ["https://example.com"]
    mock_extractor.compute_image_hash.return_value = "abcd1234"
    mock_extractor.stitch_screenshots.return_value = test_img

    result = export_one_item(1, cal, "链接", str(tmp_path), None)
    assert result is not None
    assert result["open_failed"] is False
    assert result["urls"] == ["https://example.com"]
    # Verify screenshot was saved
    assert os.path.exists(os.path.join(tmp_path, "001", "screenshot.png"))
    assert os.path.exists(os.path.join(tmp_path, "001", "meta.json"))


@patch("wechat_favorites_exporter.exporter.window_manager")
@patch("wechat_favorites_exporter.exporter.content_extractor")
@patch("wechat_favorites_exporter.exporter.pyautogui")
def test_export_one_item_preview_sufficient(mock_pyautogui, mock_extractor, mock_wm, tmp_path):
    """Test: preview has enough info, skip opening detail."""
    cal = _make_cal_data()
    test_img = Image.new("RGB", (800, 100), color="white")

    mock_extractor.ocr_extract_preview.return_value = {
        "title": "密码是1234", "source": "test", "date": "3月5日", "type_hint": ""
    }
    mock_extractor.is_preview_sufficient.return_value = True
    mock_extractor.capture_window_screenshot.return_value = test_img
    mock_extractor.compute_image_hash.return_value = "abcd1234"

    result = export_one_item(1, cal, "笔记", str(tmp_path), None)
    assert result is not None
    assert result["skipped_detail"] is True
    # Should NOT have called wait_for_new_window (no detail opened)
    mock_wm.wait_for_new_window.assert_not_called()


@patch("wechat_favorites_exporter.exporter.window_manager")
@patch("wechat_favorites_exporter.exporter.content_extractor")
@patch("wechat_favorites_exporter.exporter.pyautogui")
def test_export_one_item_window_timeout(mock_pyautogui, mock_extractor, mock_wm, tmp_path):
    """Test: click item but no window opens (timeout)."""
    cal = _make_cal_data()
    test_img = Image.new("RGB", (800, 100), color="white")

    mock_wm.get_wechat_window_count.return_value = 1
    mock_wm.wait_for_new_window.return_value = False

    mock_extractor.ocr_extract_preview.return_value = {
        "title": "Something", "source": "x", "date": "4月3日", "type_hint": "链接"
    }
    mock_extractor.is_preview_sufficient.return_value = False
    mock_extractor.capture_window_screenshot.return_value = test_img
    mock_extractor.compute_image_hash.return_value = "abcd1234"

    result = export_one_item(1, cal, "链接", str(tmp_path), None)
    assert result is not None
    assert result["open_failed"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_exporter.py::test_export_one_item_normal -v`
Expected: FAIL — ImportError (export_one_item not defined)

- [ ] **Step 3: Implement export_one_item in exporter.py**

Append to `wechat_favorites_exporter/exporter.py`:

```python
import pyautogui
from PIL import Image

from wechat_favorites_exporter import content_extractor, window_manager
from wechat_favorites_exporter.calibrator import CalibrationData
from wechat_favorites_exporter.config import (
    LONG_SCREENSHOT_OVERLAP,
    WINDOW_TIMEOUT,
    random_delay,
)


def export_one_item(
    index: int,
    cal: CalibrationData,
    category: str,
    output_dir: str,
    prev_hash: str | None,
) -> dict | None:
    """Export a single favorites item. Returns the meta dict, or None on critical failure."""
    item_dir = create_item_dir(output_dir, index)

    # Step 1: Screenshot the list item area for preview OCR
    list_item_bounds = (cal.click_x - 300, cal.click_y - 40, 600, 80)
    list_img = content_extractor.capture_window_screenshot(list_item_bounds)
    preview = content_extractor.ocr_extract_preview(list_img)

    # Step 1b: Check if preview is sufficient (skip opening detail)
    if content_extractor.is_preview_sufficient(preview):
        list_img.save(os.path.join(item_dir, "screenshot.png"))
        img_hash = content_extractor.compute_image_hash(list_img)
        meta = build_meta(
            index=index, category=category, preview=preview,
            image_hash=img_hash, skipped_detail=True,
        )
        save_item_meta(item_dir, meta)
        return meta

    # Step 2: Click the top item
    win_count = window_manager.get_wechat_window_count()
    pyautogui.click(cal.click_x, cal.click_y)

    # Step 3: Wait for new window
    if not window_manager.wait_for_new_window(win_count, timeout=WINDOW_TIMEOUT):
        # Fallback: save list screenshot
        list_img.save(os.path.join(item_dir, "screenshot.png"))
        img_hash = content_extractor.compute_image_hash(list_img)
        meta = build_meta(
            index=index, category=category, preview=preview,
            image_hash=img_hash, open_failed=True,
        )
        save_item_meta(item_dir, meta)
        return meta

    # Step 4: Wait for content to load
    random_delay()

    # Step 5: Get window bounds
    bounds = window_manager.get_front_window_bounds()
    if bounds is None:
        window_manager.close_front_window()
        meta = build_meta(
            index=index, category=category, preview=preview,
            open_failed=True, error="Could not get window bounds",
        )
        save_item_meta(item_dir, meta)
        return meta

    # Step 6: Long screenshot
    screenshots = []
    prev_shot = None
    consecutive_similar = 0
    for page in range(20):  # max 20 pages
        shot = content_extractor.capture_window_screenshot(bounds)
        if prev_shot is not None and content_extractor.images_are_similar(shot, prev_shot):
            consecutive_similar += 1
            if consecutive_similar >= 2:
                break
        else:
            consecutive_similar = 0
            screenshots.append(shot)
        prev_shot = shot
        if page < 19:  # don't scroll after last capture
            pyautogui.scroll(-5)
            import time
            time.sleep(0.3)

    if screenshots:
        overlap = int(bounds[3] * LONG_SCREENSHOT_OVERLAP) if len(screenshots) > 1 else 0
        final_img = content_extractor.stitch_screenshots(screenshots, overlap=overlap)
    else:
        final_img = content_extractor.capture_window_screenshot(bounds)

    final_img.save(os.path.join(item_dir, "screenshot.png"))

    # Step 7: Extract text
    pyautogui.hotkey("command", "a")
    import time
    time.sleep(0.2)
    pyautogui.hotkey("command", "c")
    time.sleep(0.2)
    text = content_extractor.extract_text_from_clipboard()
    if text:
        with open(os.path.join(item_dir, "content.txt"), "w", encoding="utf-8") as f:
            f.write(text)

    # Step 8: Extract URLs
    urls = content_extractor.extract_urls(text) if text else []

    # Step 9: Close detail window
    window_manager.close_front_window()

    img_hash = content_extractor.compute_image_hash(final_img)
    meta = build_meta(
        index=index, category=category, preview=preview,
        text=text, urls=urls, image_hash=img_hash,
        screenshot_pages=len(screenshots),
    )
    save_item_meta(item_dir, meta)
    return meta
```

- [ ] **Step 4: Run all exporter tests**

Run: `python -m pytest tests/test_exporter.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add wechat_favorites_exporter/exporter.py tests/test_exporter.py
git commit -m "feat: add export_one_item with full export flow, long screenshot, fallback"
```

---

### Task 7: Main CLI entry point

**Files:**
- Create: `wechat_favorites_exporter/main.py`

- [ ] **Step 1: Implement main.py**

```python
# wechat_favorites_exporter/main.py
import argparse
import os
import sys
import time

import pyautogui

from wechat_favorites_exporter.calibrator import (
    CalibrationData,
    compute_category_position,
    load_calibration,
    run_calibration,
    save_calibration,
)
from wechat_favorites_exporter.config import (
    CATEGORIES,
    END_DETECTION_COUNT,
    OUTPUT_DIR,
    load_progress,
    random_delay,
    save_progress,
)
from wechat_favorites_exporter.content_extractor import (
    capture_window_screenshot,
    compute_image_hash,
    images_are_similar,
    ocr_extract_preview,
)
from wechat_favorites_exporter.exporter import export_one_item, should_skip
from wechat_favorites_exporter.window_manager import activate_wechat

# Safety
pyautogui.FAILSAFE = True


def select_category() -> str:
    """Interactive category selection."""
    print("\n可用分类：")
    for i, cat in enumerate(CATEGORIES):
        print(f"  {i + 1}. {cat}")
    while True:
        choice = input("\n请输入分类编号: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(CATEGORIES):
                return CATEGORIES[idx]
        except ValueError:
            pass
        print("无效输入，请重试")


def main():
    parser = argparse.ArgumentParser(description="微信收藏夹批量导出工具")
    parser.add_argument("--category", type=str, help="指定分类")
    parser.add_argument("--resume", action="store_true", help="从上次中断位置继续")
    parser.add_argument("--recalibrate", action="store_true", help="强制重新校准")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR, help="导出目录")
    parser.add_argument("--delay", type=float, default=None, help="操作间隔秒数")
    args = parser.parse_args()

    output_dir = args.output_dir
    cal_path = os.path.join(output_dir, "calibration.json")
    progress_path = os.path.join(output_dir, "progress.json")

    # Category selection
    category = args.category or select_category()
    if category not in CATEGORIES:
        print(f"错误：未知分类 '{category}'")
        sys.exit(1)

    category_dir = os.path.join(output_dir, category)
    os.makedirs(category_dir, exist_ok=True)

    # Calibration
    cal = None
    if not args.recalibrate:
        cal = load_calibration(cal_path)
        if cal:
            use_existing = input(f"发现已有校准数据，是否使用？(y/n): ").strip().lower()
            if use_existing != "y":
                cal = None
    if cal is None:
        cal = run_calibration()
        save_calibration(cal, cal_path)

    # Resume check
    start_index = 1
    if args.resume:
        progress = load_progress(progress_path)
        if progress and progress.get("category") == category:
            start_index = progress["last_completed_index"] + 1
            print(f"从第 {start_index} 条继续")

    # Navigate to category
    activate_wechat()
    time.sleep(0.5)
    cat_pos = compute_category_position(cal, category)
    if cat_pos:
        pyautogui.click(cat_pos[0], cat_pos[1])
        time.sleep(1.0)

    # Skip to start_index if resuming
    if start_index > 1:
        print(f"跳过前 {start_index - 1} 条...")
        for _ in range(start_index - 1):
            pyautogui.scroll(-3)
            time.sleep(0.15)
        time.sleep(0.5)

    # Main export loop
    print(f"\n开始导出分类「{category}」...")
    index = start_index
    consecutive_end = 0
    prev_hash = None
    exported = 0
    skipped = 0
    failed = 0

    try:
        while True:
            # Check if already exported (smart skip)
            list_bounds = (cal.click_x - 300, cal.click_y - 40, 600, 80)
            list_img = capture_window_screenshot(list_bounds)
            preview = ocr_extract_preview(list_img)

            if should_skip(index, preview, category_dir):
                print(f"  [{index}] 已导出，跳过")
                skipped += 1
            else:
                # Export
                try:
                    meta = export_one_item(index, cal, category, category_dir, prev_hash)
                    if meta:
                        prev_hash = meta.get("image_hash")
                        status = "跳过详情" if meta.get("skipped_detail") else "OK"
                        if meta.get("open_failed"):
                            status = "打开失败(已截图)"
                            failed += 1
                        else:
                            exported += 1
                        title = meta.get("preview", {}).get("title", "")[:30]
                        print(f"  [{index}] {status} - {title}")

                        # End detection
                        if prev_hash and images_are_similar(list_img, list_img):
                            consecutive_end += 1
                        else:
                            consecutive_end = 0

                        if consecutive_end >= END_DETECTION_COUNT:
                            print("\n检测到已到达列表末尾")
                            break
                except Exception as e:
                    print(f"  [{index}] 错误: {e}")
                    failed += 1

            # Save progress
            save_progress({
                "category": category,
                "last_completed_index": index,
                "started_at": load_progress(progress_path).get("started_at", time.strftime("%Y-%m-%dT%H:%M:%S")) if load_progress(progress_path) else time.strftime("%Y-%m-%dT%H:%M:%S"),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }, progress_path)

            # Scroll to next item
            pyautogui.scroll(-3)
            random_delay()
            index += 1

    except KeyboardInterrupt:
        print("\n\n用户中断，进度已保存")
    except pyautogui.FailSafeException:
        print("\n\n安全停止（鼠标移到屏幕左上角），进度已保存")

    # Summary
    print(f"\n=== 导出完成 ===")
    print(f"分类: {category}")
    print(f"成功导出: {exported}")
    print(f"跳过(已导出): {skipped}")
    print(f"失败: {failed}")
    print(f"导出目录: {os.path.abspath(category_dir)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the module imports work**

Run: `cd /Users/linux/Documents/NotesAssistant && python -c "from wechat_favorites_exporter.main import main; print('import ok')"`
Expected: `import ok`

- [ ] **Step 3: Verify --help works**

Run: `cd /Users/linux/Documents/NotesAssistant && python -m wechat_favorites_exporter.main --help`
Expected: Shows usage text with all options

- [ ] **Step 4: Commit**

```bash
git add wechat_favorites_exporter/main.py
git commit -m "feat: add main CLI entry point with category selection, resume, calibration"
```

---

### Task 8: Run full test suite and fix any issues

- [ ] **Step 1: Run entire test suite**

Run: `cd /Users/linux/Documents/NotesAssistant && python -m pytest tests/ -v --tb=short`
Expected: All tests pass (at least 26 tests)

- [ ] **Step 2: Fix any failures**

If any tests fail, read the error, fix the code, re-run until all pass.

- [ ] **Step 3: Run a quick smoke test (dry import check)**

Run:
```bash
cd /Users/linux/Documents/NotesAssistant && python -c "
from wechat_favorites_exporter.config import CATEGORIES, random_delay, save_progress, load_progress
from wechat_favorites_exporter.window_manager import get_wechat_window_count, close_front_window
from wechat_favorites_exporter.calibrator import CalibrationData, save_calibration, load_calibration
from wechat_favorites_exporter.content_extractor import extract_urls, compute_image_hash, stitch_screenshots
from wechat_favorites_exporter.exporter import should_skip, build_meta, export_one_item
from wechat_favorites_exporter.main import main
print('All imports OK')
"
```
Expected: `All imports OK`

- [ ] **Step 4: Commit if any fixes were made**

```bash
git add -A
git commit -m "fix: resolve test failures from full suite run"
```

---

### Task 9: Integration test with mock UI

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration test: simulate a 3-item export flow with all mocks."""
import json
import os
from unittest.mock import patch, MagicMock

from PIL import Image

from wechat_favorites_exporter.calibrator import CalibrationData
from wechat_favorites_exporter.exporter import export_one_item, should_skip


def _cal():
    return CalibrationData(
        category_start_pos=(100, 200),
        first_item_pos=(550, 150),
        list_bottom_pos=(550, 700),
        visible_count=5,
    )


@patch("wechat_favorites_exporter.exporter.window_manager")
@patch("wechat_favorites_exporter.exporter.content_extractor")
@patch("wechat_favorites_exporter.exporter.pyautogui")
def test_three_item_export_flow(mock_pyautogui, mock_ext, mock_wm, tmp_path):
    cal = _cal()
    items = [
        {"title": "密码1234", "type_hint": "", "should_open": False},
        {"title": "Article Link", "type_hint": "链接", "should_open": True},
        {"title": "Photo Set", "type_hint": "链接", "should_open": True},
    ]

    for i, item in enumerate(items):
        index = i + 1
        test_img = Image.new("RGB", (800, 600), color=(i * 80, 100, 100))

        mock_ext.ocr_extract_preview.return_value = {
            "title": item["title"], "source": "test",
            "date": "3月5日", "type_hint": item["type_hint"],
        }
        mock_ext.is_preview_sufficient.return_value = not item["should_open"]
        mock_ext.capture_window_screenshot.return_value = test_img
        mock_ext.compute_image_hash.return_value = f"hash{index}"
        mock_ext.images_are_similar.return_value = False
        mock_ext.extract_text_from_clipboard.return_value = f"text {index}"
        mock_ext.extract_urls.return_value = []
        mock_ext.stitch_screenshots.return_value = test_img

        mock_wm.get_wechat_window_count.return_value = 1
        mock_wm.wait_for_new_window.return_value = True
        mock_wm.get_front_window_bounds.return_value = (100, 100, 800, 600)

        meta = export_one_item(index, cal, "全部收藏", str(tmp_path), None)
        assert meta is not None
        assert os.path.exists(os.path.join(tmp_path, f"{index:03d}", "screenshot.png"))
        assert os.path.exists(os.path.join(tmp_path, f"{index:03d}", "meta.json"))

    # Verify smart skip works for already-exported items
    mock_ext.ocr_extract_preview.return_value = {
        "title": "密码1234", "source": "test", "date": "3月5日", "type_hint": "",
    }
    assert should_skip(1, {"title": "密码1234", "date": "3月5日"}, str(tmp_path)) is True
    assert should_skip(1, {"title": "different", "date": "3月5日"}, str(tmp_path)) is False
```

- [ ] **Step 2: Run integration test**

Run: `python -m pytest tests/test_integration.py -v`
Expected: 1 passed

- [ ] **Step 3: Run full suite one final time**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test for 3-item export flow with smart skip"
```

---

### Task 10: Final verification and cleanup

- [ ] **Step 1: Verify project structure**

Run: `find wechat_favorites_exporter tests -type f | sort`
Expected output:
```
tests/__init__.py
tests/test_calibrator.py
tests/test_config.py
tests/test_content_extractor.py
tests/test_exporter.py
tests/test_integration.py
tests/test_window_manager.py
wechat_favorites_exporter/__init__.py
wechat_favorites_exporter/calibrator.py
wechat_favorites_exporter/config.py
wechat_favorites_exporter/content_extractor.py
wechat_favorites_exporter/exporter.py
wechat_favorites_exporter/main.py
wechat_favorites_exporter/window_manager.py
```

- [ ] **Step 2: Run final test suite with coverage summary**

Run: `python -m pytest tests/ -v --tb=short -q`
Expected: All tests pass, 0 failures

- [ ] **Step 3: Verify CLI help**

Run: `python -m wechat_favorites_exporter.main --help`
Expected: Shows usage

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final verification, all tests passing"
```
