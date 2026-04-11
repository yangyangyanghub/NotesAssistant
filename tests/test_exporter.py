import json
import os

from unittest.mock import patch, MagicMock
from PIL import Image
from wechat_favorites_exporter.exporter import should_skip, save_item_meta, create_item_dir, export_one_item
from wechat_favorites_exporter.calibrator import CalibrationData


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
    meta = {"index": 1, "preview": {"title": "密码是1234", "date": "3月5日"}}
    with open(item_dir / "meta.json", "w") as f:
        json.dump(meta, f)
    preview = {"title": "密码是1234", "date": "3月5日"}
    assert should_skip(1, preview, str(tmp_path)) is True


def test_should_skip_mismatched_meta(tmp_path):
    item_dir = tmp_path / "001"
    item_dir.mkdir()
    meta = {"index": 1, "preview": {"title": "other title", "date": "3月5日"}}
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
    cal = _make_cal_data()
    test_img = Image.new("RGB", (800, 600), color="white")
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
    assert os.path.exists(os.path.join(tmp_path, "001", "screenshot.png"))
    assert os.path.exists(os.path.join(tmp_path, "001", "meta.json"))


@patch("wechat_favorites_exporter.exporter.window_manager")
@patch("wechat_favorites_exporter.exporter.content_extractor")
@patch("wechat_favorites_exporter.exporter.pyautogui")
def test_export_one_item_preview_sufficient(mock_pyautogui, mock_extractor, mock_wm, tmp_path):
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
    mock_wm.wait_for_new_window.assert_not_called()


@patch("wechat_favorites_exporter.exporter.window_manager")
@patch("wechat_favorites_exporter.exporter.content_extractor")
@patch("wechat_favorites_exporter.exporter.pyautogui")
def test_export_one_item_window_timeout(mock_pyautogui, mock_extractor, mock_wm, tmp_path):
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
