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
    assert data.list_area_height == 550
    assert data.scroll_amount == 440
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
    x, y = compute_category_position(data, "链接")
    assert x == 100
    assert y == 200 + 2 * 56


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
