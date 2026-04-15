from rapidocr_onnxruntime import RapidOCR
from PIL import Image
import numpy as np
import re

for i in range(3):
    try:
        img = Image.open(f'output/全部收藏/{i:03d}/screenshot.png')
        ocr = RapidOCR()
        result, _ = ocr(np.array(img))
        
        if result:
            all_text = ' '.join([line[1] for line in result])
            urls = re.findall(r'https?://[^\s<>"]+', all_text)
            print(f'Item {i:03d}: screenshot size={img.size}, found {len(urls)} URL(s)')
            for url in urls:
                print(f'  URL: {url}')
        else:
            print(f'Item {i:03d}: no OCR results')
    except Exception as e:
        print(f'Item {i:03d}: error - {e}')
