import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import re
from rapidocr_onnxruntime import RapidOCR
from PIL import Image
import numpy as np

for i in range(3):
    img = Image.open(f'output/全部收藏/{i:03d}/screenshot.png')
    ocr = RapidOCR()
    result, _ = ocr(np.array(img))
    texts = [line[1] for line in (result or [])]
    full = '\n'.join(texts)
    
    # Find URLs
    urls = re.findall(r'https?://[^\s<>"]+', full)
    
    print(f'Item {i:03d}:')
    print(f'  OCR lines: {len(texts)}')
    print(f'  Preview: {texts[:3]}')
    if urls:
        print(f'  URLs found: {urls}')
    print()
