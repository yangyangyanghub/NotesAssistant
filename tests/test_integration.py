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
    assert should_skip(1, {"title": "密码1234", "date": "3月5日"}, str(tmp_path)) is True
    assert should_skip(1, {"title": "different", "date": "3月5日"}, str(tmp_path)) is False
