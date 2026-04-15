import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
import json
from rapidocr_onnxruntime import RapidOCR
from PIL import Image
import numpy as np

print('Checking all exported items for URLs...')

for i in range(5):
    filepath = f'output/全部收藏/{i:03d}/screenshot.png'
    try:
        img = Image.open(filepath)
        ocr = RapidOCR()
        result, _ = ocr(np.array(img))
        texts = [line[1] for line in (result or [])]
        full = '\n'.join(texts)
        
        # Find URLs
        urls = re.findall(r'https?://[^\s<>"]+', full)
        
        print(f'\nItem {i:03d}:')
        print(f'  Screenshot: {img.size}')
        print(f'  OCR lines: {len(texts)}')
        if texts:
            print(f'  Top 3 lines: {texts[:3]}')
        if urls:
            print(f'  URLs: {urls}')
        else:
            print(f'  URLs: NONE in screenshot')
        
        # Check meta.json
        meta_path = f'output/全部收藏/{i:03d}/meta.json'
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                if meta.get('urls'):
                    print(f'  Meta URLs: {meta["urls"]}')
        except Exception:
            pass
            
    except Exception as e:
        print(f'Item {i:03d}: Error - {e}')
