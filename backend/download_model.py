import os
from modelscope import snapshot_download

def main():
    model_id = 'Qwen/Qwen3-ASR-1.7B'
    
    # 获取当前脚本所在目录，并在该目录下创建 models/Qwen3-ASR-1.7B 文件夹用于存放模型
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_dir = os.path.join(base_dir, 'models', 'Qwen3-ASR-1.7B')
    
    print("==================================================")
    print(f"开始通过 ModelScope 下载模型: {model_id}")
    print(f"模型将保存至本地目录: {local_dir}")
    print("这可能需要几分钟的时间，请耐心等待（约 3.4 GB）...")
    print("==================================================")
    
    # 下载模型
    try:
        model_dir = snapshot_download(model_id, local_dir=local_dir)
        print("\n==================================================")
        print(f"✅ 模型下载并完整校验成功！")
        print(f"✅ 本地路径: {model_dir}")
        print("✅ 您现在可以运行 main.py 来启动后端服务了。")
        print("==================================================")
    except Exception as e:
        print(f"\n❌ 下载模型时出现错误: {str(e)}")

if __name__ == "__main__":
    main()
