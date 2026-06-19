import os
import sys
import json
from pathlib import Path

# 从 api_key.json 读取豆包 API Key（exe 同级目录或源码目录）
def load_api_key():
    """加载 API Key，支持 exe 运行和源码运行"""
    # 获取程序所在目录
    if getattr(sys, 'frozen', False):
        # exe 运行时 - 优先从 exe 同级目录读取（dist/ASR_Floating_App）
        base_dir = Path(os.path.dirname(sys.executable))
    else:
        # 源码运行时
        base_dir = Path(__file__).parent
    
    # 先在 base_dir 查找 api_key.json
    json_file = base_dir / "api_key.json"
    
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("doubao_api_key", "")
        except Exception:
            pass
    
    # 如果找不到，尝试在 base_dir/_internal 查找（PyInstaller 打包的情况）
    if getattr(sys, 'frozen', False):
        internal_json = base_dir / "_internal" / "api_key.json"
        if internal_json.exists():
            try:
                with open(internal_json, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("doubao_api_key", "")
            except Exception:
                pass
    
    # 如果都找不到，返回空字符串
    return ""

DOUBAO_API_KEY = load_api_key()

def load_local_config():
    """加载本地后端相关配置"""
    if getattr(sys, 'frozen', False):
        base_dir = Path(os.path.dirname(sys.executable))
    else:
        base_dir = Path(__file__).parent
    
    json_file = base_dir / "api_key.json"
    
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {
                    "local_backend_url": config.get("local_backend_url", "http://localhost:8000"),
                    "asr_provider": config.get("asr_provider", "doubao"),
                    "local_model": config.get("local_model", "qwen"),
                    "save_folder": config.get("save_folder", ""),
                    "hotkey_enabled": config.get("hotkey_enabled", False),
                    "hotkey_key": config.get("hotkey_key", ""),
                }
        except Exception:
            pass
    
    if getattr(sys, 'frozen', False):
        internal_json = base_dir / "_internal" / "api_key.json"
        if internal_json.exists():
            try:
                with open(internal_json, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return {
                        "local_backend_url": config.get("local_backend_url", "http://localhost:8000"),
                        "asr_provider": config.get("asr_provider", "doubao"),
                        "local_model": config.get("local_model", "qwen"),
                        "save_folder": config.get("save_folder", ""),
                        "hotkey_enabled": config.get("hotkey_enabled", False),
                        "hotkey_key": config.get("hotkey_key", ""),
                    }
            except Exception:
                pass
    
    return {
        "local_backend_url": "http://localhost:8000",
        "asr_provider": "doubao",
        "local_model": "qwen",
        "save_folder": "",
        "hotkey_enabled": False,
        "hotkey_key": "",
    }

_local_config = load_local_config()
LOCAL_BACKEND_URL = _local_config["local_backend_url"]
ASR_PROVIDER = _local_config["asr_provider"]
LOCAL_MODEL = _local_config["local_model"]
SAVE_FOLDER = _local_config["save_folder"]
HOTKEY_ENABLED = _local_config["hotkey_enabled"]
HOTKEY_KEY = _local_config["hotkey_key"]

def save_settings(settings: dict):
    """保存设置到 api_key.json"""
    if getattr(sys, 'frozen', False):
        base_dir = Path(os.path.dirname(sys.executable))
    else:
        base_dir = Path(__file__).parent

    json_file = base_dir / "api_key.json"

    # 读取现有配置
    config = {}
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass

    # 更新设置
    config.update(settings)

    # 写回
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


# 临时文件目录
TEMP_DIR = Path(os.environ.get('TEMP', '/tmp')) / "asr_floating_app"
os.makedirs(TEMP_DIR, exist_ok=True)
TEMP_WAV_FILE = str(TEMP_DIR / "temp_record.wav")
