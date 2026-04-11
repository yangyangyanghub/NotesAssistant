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
    counts = [2, 2, 3]
    mock_results = [MagicMock(stdout=f"{c}\n", returncode=0) for c in counts]
    with patch("subprocess.run", side_effect=mock_results):
        with patch("time.sleep"):
            result = wait_for_new_window(2, timeout=5.0)
            assert result is True


def test_wait_for_new_window_timeout():
    mock_result = MagicMock(stdout="2\n", returncode=0)
    with patch("subprocess.run", return_value=mock_result):
        with patch("time.sleep"):
            with patch("time.time", side_effect=[0, 0.5, 1.0, 5.1]):
                result = wait_for_new_window(2, timeout=5.0)
                assert result is False
