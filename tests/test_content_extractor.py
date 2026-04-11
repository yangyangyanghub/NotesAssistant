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
    assert result.size == (400, 540)


def test_stitch_screenshots_overlap_crops_correctly():
    img1 = Image.new("RGB", (200, 100), color="red")
    img2 = Image.new("RGB", (200, 100), color="blue")
    result = stitch_screenshots([img1, img2], overlap=20)
    assert result.getpixel((100, 10)) == (255, 0, 0)
    assert result.getpixel((100, 170)) == (0, 0, 255)
