import numpy as np
from PIL import Image
from base64 import b64encode
from datetime import datetime
import json
import requests

image_batch = []
for i, color in enumerate(['red', 'green', 'blue']):
    pil_image = Image.new('RGB', (1920,1080), color=color)
    pil_image.save(f'{color}.jpg')

    with open(f'{color}.jpg', 'rb') as f:
        image = {
            'file'      : b64encode(f.read()).decode('utf-8'),
            'timestamp' : f'{datetime.now()}',
            'store_name': 'Caper',
            'camera_id' : f'{i}',
            'barcode'   : f'{i}'
        }

        image_batch.append(image)

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
r = requests.post('http://localhost:5000/upload_image_batch',
                  headers=headers,
                  data=json.dumps(image_batch))

print(r.status_code)
