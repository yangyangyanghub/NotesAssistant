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
