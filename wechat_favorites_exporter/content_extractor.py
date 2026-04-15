import re

from PIL import Image


def extract_urls(text: str) -> list[str]:
    pattern = r'https?://[^\s<>"\'\]）》，。、\u4e00-\u9fff]+'
    return re.findall(pattern, text)


def compute_image_hash(image: Image.Image) -> str:
    # Pack 8 pixel luminance values (sampled from an 8x8 thumbnail) into a
    # 64-bit hex string.  Using raw luminance rather than a comparison-based
    # hash ensures that uniformly-coloured images with different colours
    # produce distinct hashes.
    small = image.resize((8, 8)).convert("L")
    pixels = list(small.getdata())  # 64 values, each 0-255
    # Take every 8th pixel (8 samples) and encode as two hex nibbles each.
    sampled = pixels[::8][:8]  # exactly 8 values
    return "".join(f"{p:02x}" for p in sampled)


def images_are_similar(img1: Image.Image, img2: Image.Image, threshold: int = 5) -> bool:
    h1 = compute_image_hash(img1)
    h2 = compute_image_hash(img2)
    diff = bin(int(h1, 16) ^ int(h2, 16)).count("1")
    return diff <= threshold


def is_preview_sufficient(preview: dict) -> bool:
    type_hint = preview.get("type_hint", "").strip()
    skip_hints = ["DOCX", "PDF", "XLSX", "PPT", "链接", "KB", "MB", "http"]
    if any(h in type_hint for h in skip_hints):
        return False
    title = preview.get("title", "")
    if title and len(title) < 200 and "http" not in title:
        return True
    return False


def stitch_screenshots(images: list[Image.Image], overlap: int = 0) -> Image.Image:
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
    from PIL import ImageGrab
    x, y, w, h = bounds
    bbox = (x, y, x + w, y + h)
    return ImageGrab.grab(bbox=bbox)


def extract_text_from_clipboard() -> str | None:
    try:
        import pyperclip

        text = pyperclip.paste()
        return text if text else None
    except Exception:
        return None


def ocr_extract_preview(image: Image.Image) -> dict:
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
        if re.search(r'\d+月\d+日|星期', line):
            date = line
        elif re.search(r'(DOCX|PDF|XLSX|PPT|KB|MB)', line, re.IGNORECASE):
            type_hint = line
        elif not source:
            source = line
    return {"title": title, "source": source, "date": date, "type_hint": type_hint}
