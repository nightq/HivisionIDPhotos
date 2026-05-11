import argparse
import os
import sys
from demo.processor import IDPhotoProcessor
from demo.ui import create_ui
from hivision.creator.choose_handler import HUMAN_MATTING_MODELS


def check_and_download_models(weights_dir: str) -> None:
    """检查模型是否存在，如不存在则自动下载（适用于打包后的exe）"""
    # 检查是否有模型文件
    has_models = any(
        file.endswith(".onnx") or file.endswith(".mnn")
        for file in os.listdir(weights_dir)
        if os.path.isfile(os.path.join(weights_dir, file))
    )

    if not has_models:
        print("=" * 60)
        print("未检测到模型文件，正在自动下载...")
        print("=" * 60)
        try:
            import subprocess

            # 确定脚本路径（兼容打包后的exe环境）
            if getattr(sys, "frozen", False):
                # PyInstaller 打包后运行时
                base_path = sys._MEIPASS
                script_path = os.path.join(base_path, "scripts", "download_model.py")
                # 如果不在打包目录，尝试用当前目录
                if not os.path.exists(script_path):
                    script_path = os.path.join(
                        os.path.dirname(sys.executable), "scripts", "download_model.py"
                    )
            else:
                # 开发环境直接运行
                script_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "scripts",
                    "download_model.py",
                )

            # 如果脚本不存在，使用简化下载方式
            if not os.path.exists(script_path):
                print("正在下载默认模型 hivision_modnet...")
                import urllib.request

                os.makedirs(weights_dir, exist_ok=True)
                model_path = os.path.join(weights_dir, "hivision_modnet.onnx")

                # 多个下载源，自动重试
                download_urls = [
                    # GitHub 源
                    "https://github.com/Zeyi-Lin/HivisionIDPhotos/releases/download/pretrained-model/hivision_modnet.onnx",
                    # ModelScope 国内镜像
                    "https://modelscope.cn/api/v1/models/AI-ModelScope/hivision_modnet/repo?FileName=hivision_modnet.onnx",
                    # SwanHub 镜像
                    "https://swanhub.co/api/v1/models/ZeyiLin/HivisionIDPhotos_models/repo?FileName=hivision_modnet.onnx",
                ]

                for i, url in enumerate(download_urls, 1):
                    try:
                        print(f"尝试下载源 {i}/{len(download_urls)}...")
                        urllib.request.urlretrieve(url, model_path)
                        # 验证文件大小（约25MB）
                        if os.path.getsize(model_path) > 1000000:  # > 1MB 才算下载成功
                            print("模型下载完成！")
                            break
                        else:
                            print(f"源 {i} 下载文件不完整，尝试下一个...")
                            os.remove(model_path)
                    except Exception as e:
                        print(f"源 {i} 下载失败: {str(e)[:50]}...")
                        if i == len(download_urls):
                            raise
                        continue
            else:
                # 运行下载脚本
                subprocess.run(
                    [sys.executable, script_path, "--models", "hivision_modnet"],
                    check=True,
                )
            print("=" * 60)
            print("模型下载完成，正在启动服务...")
            print("=" * 60)
        except Exception as e:
            print(f"\n自动下载失败: {e}")
            print("\n" + "=" * 60)
            print("【解决方案】请手动下载模型文件")
            print("=" * 60)
            print("\n1. 下载 hivision_modnet.onnx (25MB):")
            print("   - GitHub: https://github.com/Zeyi-Lin/HivisionIDPhotos/releases")
            print("   - SwanHub: https://swanhub.co/ZeYiLin/HivisionIDPhotos_models/tree/main")
            print("\n2. 将下载的文件放到这个目录:")
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else root_dir
            model_dir = os.path.join(exe_dir, "hivision", "creator", "weights")
            print(f"   {model_dir}")
            print("\n3. 重新运行程序")
            print("\n也可以将模型文件放在 exe 同目录下的 hivision/creator/weights 文件夹")
            print("=" * 60)
            input("\n按回车键退出...")
            sys.exit(1)


# 确定根目录（兼容打包后的exe环境）
if getattr(sys, "frozen", False):
    # PyInstaller 打包后运行时
    root_dir = sys._MEIPASS
else:
    # 开发环境
    root_dir = os.path.dirname(os.path.abspath(__file__))

# 模型目录
weights_dir = os.path.join(root_dir, "hivision", "creator", "weights")
os.makedirs(weights_dir, exist_ok=True)

# 检查并自动下载模型
check_and_download_models(weights_dir)

# 获取存在的人像分割模型列表
# 通过检查 hivision/creator/weights 目录下的 .onnx 和 .mnn 文件
# 只保留文件名（不包括扩展名）
HUMAN_MATTING_MODELS_EXIST = [
    os.path.splitext(file)[0]
    for file in os.listdir(weights_dir)
    if file.endswith(".onnx") or file.endswith(".mnn")
]
# 在HUMAN_MATTING_MODELS中的模型才会被加载到Gradio中显示
HUMAN_MATTING_MODELS_CHOICE = [
    model for model in HUMAN_MATTING_MODELS if model in HUMAN_MATTING_MODELS_EXIST
]

if len(HUMAN_MATTING_MODELS_CHOICE) == 0:
    raise ValueError(
        "未找到任何存在的人像分割模型，请检查 hivision/creator/weights 目录下的文件"
        + "\n"
        + "No existing portrait segmentation model was found, please check the files in the hivision/creator/weights directory."
    )

FACE_DETECT_MODELS = ["face++ (联网Online API)", "mtcnn"]
FACE_DETECT_MODELS_EXPAND = (
    ["retinaface-resnet50"]
    if os.path.exists(
        os.path.join(
            root_dir, "hivision/creator/retinaface/weights/retinaface-resnet50.onnx"
        )
    )
    else []
)
FACE_DETECT_MODELS_CHOICE = FACE_DETECT_MODELS + FACE_DETECT_MODELS_EXPAND

LANGUAGE = ["zh", "en", "ko", "ja"]

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--port", type=int, default=7860, help="The port number of the server"
    )
    argparser.add_argument(
        "--host", type=str, default="127.0.0.1", help="The host of the server"
    )
    argparser.add_argument(
        "--root_path",
        type=str,
        default=None,
        help="The root path of the server, default is None (='/'), e.g. '/myapp'",
    )
    args = argparser.parse_args()

    processor = IDPhotoProcessor()

    demo = create_ui(
        processor,
        root_dir,
        HUMAN_MATTING_MODELS_CHOICE,
        FACE_DETECT_MODELS_CHOICE,
        LANGUAGE,
    )
    
    # 如果RUN_MODE是Beast，打印已开启野兽模式
    if os.getenv("RUN_MODE") == "beast":
        print("[Beast mode activated.] 已开启野兽模式。")

    demo.launch(
        server_name=args.host,
        server_port=args.port,
        favicon_path=os.path.join(root_dir, "assets/hivision_logo.png"),
        root_path=args.root_path,
    )
