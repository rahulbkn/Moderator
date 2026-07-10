#!/usr/bin/env bash
set -e

pip install -r requirements.txt

python -c "
import urllib.request
from pathlib import Path
model_dir = Path.home() / '.nudenet'
model_dir.mkdir(parents=True, exist_ok=True)
model_path = model_dir / 'default.onnx'
if not model_path.exists():
    print('Downloading NudeNet model...')
    urllib.request.urlretrieve(
        'https://github.com/notAI-tech/NudeNet/releases/download/v3.4.2/default.onnx',
        model_path
    )
    print('Model downloaded')
else:
    print('Model already cached')
"
