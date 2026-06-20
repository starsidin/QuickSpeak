import os
import sys
import json
from pathlib import Path

# ---- 路径工具 ----

def get_base_dir():
    """获取程序所在目录"""
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    else:
        return Path(__file__).parent

def get_data_dir():
    """获取 Portable 数据目录，统一存放配置和临时文件"""
    base = get_base_dir()
    data_dir = base / "data"
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_config_path():
    return get_data_dir() / "config.json"

def get_legacy_config_paths():
    """旧版配置文件位置，用于迁移"""
    base = get_base_dir()
    paths = [base / "api_key.json"]
    if getattr(sys, 'frozen', False):
        paths.append(base / "_internal" / "api_key.json")
    return paths

# ---- 配置加载 / 保存 ----

def _load_raw_config():
    """加载配置，优先 data/config.json，其次尝试从旧位置迁移"""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    # 尝试从旧位置迁移
    for legacy in get_legacy_config_paths():
        if legacy.exists():
            try:
                with open(legacy, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 写入新位置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                return config
            except Exception:
                pass

    return {}

_raw_config = _load_raw_config()

# Whisper 已舍弃：旧配置自动回退到 Qwen，避免升级后继续进入禁用路径。
if _raw_config.get("local_model") == "whisper":
    _raw_config["local_model"] = "qwen"

# ---- 对外暴露的配置项 ----

DOUBAO_API_KEY = _raw_config.get("doubao_api_key", "")
LOCAL_BACKEND_URL = _raw_config.get("local_backend_url", "http://localhost:8000")
ASR_PROVIDER = _raw_config.get("asr_provider", "doubao")
LOCAL_MODEL = _raw_config.get("local_model", "qwen")
SAVE_FOLDER = _raw_config.get("save_folder", "")
HOTKEY_ENABLED = _raw_config.get("hotkey_enabled", False)
HOTKEY_KEY = _raw_config.get("hotkey_key", "")
MICROPHONE_DEVICE = _raw_config.get("microphone_device", "")  # 设备名称或索引

def save_settings(settings: dict):
    """保存设置到 data/config.json"""
    config_path = get_config_path()

    config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass

    config.update(settings)

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


# ---- 临时文件目录 ----

TEMP_DIR = get_data_dir() / "temp"
os.makedirs(TEMP_DIR, exist_ok=True)
TEMP_WAV_FILE = str(TEMP_DIR / "temp_record.wav")
AUTO_SAVE_FILE = str(TEMP_DIR / "autosave_content.txt")  # 自动保存的创作内容


# ---- 应用元信息 ----

APP_NAME = "QuickSpeak"
APP_DISPLAY_NAME = "说记"
APP_VERSION = "1.0.2"
APP_AUTHOR = "Ranklee Studio"
