import platform
import subprocess
import sys
import time

# 根据平台选择窗口管理实现
_IS_MACOS = platform.system() == "Darwin"
_IS_WINDOWS = platform.system() == "Windows"

# 窗口标题配置
WECHAT_WINDOW_TITLE_MAC = "WeChat"
WECHAT_WINDOW_TITLE_WIN = "微信"  # Windows 版微信窗口标题


def _run_applescript(script: str) -> subprocess.CompletedProcess:
    """执行 AppleScript（仅 macOS）"""
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10,
    )


def _get_wechat_windows_win():
    """获取所有微信窗口句柄（Windows）"""
    import win32gui

    windows = []

    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            # Match exact title or partial match (in case of encoding issues)
            if title == WECHAT_WINDOW_TITLE_WIN or "微" in title or "WeChat" in title:
                windows.append(hwnd)
        return True

    win32gui.EnumWindows(enum_callback, None)

    # If still no windows found, try by class name
    if not windows:
        # Common WeChat window class names
        for class_name in ["WeixinMainWnd", "WeChatMainWnd", "WeChat_App_Window_With_Message"]:
            hwnd = win32gui.FindWindow(class_name, None)
            if hwnd and win32gui.IsWindowVisible(hwnd):
                windows.append(hwnd)

    return windows


def _get_front_window_win():
    """获取当前激活的微信窗口句柄（Windows）"""
    import win32gui

    windows = _get_wechat_windows_win()
    if not windows:
        return None

    # 优先返回非最小化的窗口
    active_windows = []
    for hwnd in windows:
        try:
            if not win32gui.IsIconic(hwnd):  # 不是最小化状态
                active_windows.append(hwnd)
        except Exception:
            pass

    if active_windows:
        # 如果有多个非最小化窗口，返回第一个（通常是主窗口）
        return active_windows[0]

    # 如果都最小化了，返回最后一个
    return windows[-1] if windows else None


def get_wechat_window_count() -> int:
    """获取微信窗口数量"""
    if _IS_MACOS:
        script = f'''
        tell application "System Events"
            tell process "{WECHAT_WINDOW_TITLE_MAC}"
                return count of windows
            end tell
        end tell
        '''
        result = _run_applescript(script)
        try:
            return int(result.stdout.strip())
        except (ValueError, AttributeError):
            return 0

    elif _IS_WINDOWS:
        return len(_get_wechat_windows_win())

    return 0


def get_front_window_bounds() -> tuple[int, int, int, int] | None:
    """获取前台窗口位置和大小，返回 (x, y, width, height)"""
    if _IS_MACOS:
        script = f'''
        tell application "System Events"
            tell process "{WECHAT_WINDOW_TITLE_MAC}"
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

    elif _IS_WINDOWS:
        import win32gui

        hwnd = _get_front_window_win()
        if hwnd is not None:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                # rect = (left, top, right, bottom)
                x, y = rect[0], rect[1]
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                return (x, y, width, height)
            except Exception:
                return None

        # Fallback: get the actual foreground window (any app, not just WeChat)
        try:
            fg_hwnd = win32gui.GetForegroundWindow()
            if fg_hwnd:
                rect = win32gui.GetWindowRect(fg_hwnd)
                x, y = rect[0], rect[1]
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                # Only return if it's a reasonable size (not a tiny popup)
                if width > 400 and height > 300:
                    return (x, y, width, height)
        except Exception:
            pass

    return None


def close_front_window() -> None:
    """关闭前台窗口"""
    if _IS_MACOS:
        script = '''
        tell application "System Events"
            tell process "WeChat"
                keystroke "w" using command down
            end tell
        end tell
        '''
        _run_applescript(script)

    elif _IS_WINDOWS:
        import win32gui
        import win32con

        hwnd = _get_front_window_win()
        if hwnd is not None:
            # 发送 WM_CLOSE 消息关闭窗口
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            time.sleep(0.3)


def activate_wechat() -> None:
    """激活微信窗口"""
    if _IS_MACOS:
        script = f'tell application "{WECHAT_WINDOW_TITLE_MAC}" to activate'
        _run_applescript(script)

    elif _IS_WINDOWS:
        import win32gui

        hwnd = _get_front_window_win()
        if hwnd is not None:
            try:
                # 如果窗口最小化，先恢复
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, 9)  # SW_RESTORE
                else:
                    win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.3)
            except Exception:
                pass


def wait_for_new_window(original_count: int, timeout: float = 5.0) -> bool:
    """等待新窗口弹出"""
    start = time.time()
    while time.time() - start < timeout:
        current = get_wechat_window_count()
        if current > original_count:
            return True
        time.sleep(0.3)
    return False
