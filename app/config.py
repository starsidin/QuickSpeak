import os
from pathlib import Path

# 基本配置
ASR_BASE_URL = "http://localhost:8000/v1"
ASR_MODEL = ""  # 如果为空，会自动从 /v1/models 获取可用模型；如果是 qwen asr 1.7b，也可手动填入模型名

# 临时文件目录
TEMP_DIR = Path(os.environ.get('TEMP', '/tmp')) / "asr_floating_app"
os.makedirs(TEMP_DIR, exist_ok=True)
TEMP_WAV_FILE = str(TEMP_DIR / "temp_record.wav")
