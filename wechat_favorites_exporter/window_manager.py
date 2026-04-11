import subprocess
import time


def _run_applescript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10,
    )


def get_wechat_window_count() -> int:
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
    script = '''
    tell application "System Events"
        tell process "WeChat"
            keystroke "w" using command down
        end tell
    end tell
    '''
    _run_applescript(script)


def activate_wechat() -> None:
    script = 'tell application "WeChat" to activate'
    _run_applescript(script)


def wait_for_new_window(original_count: int, timeout: float = 5.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        current = get_wechat_window_count()
        if current > original_count:
            return True
        time.sleep(0.3)
    return False
