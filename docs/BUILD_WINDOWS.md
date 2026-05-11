# Windows 打包指南

本文档说明如何将 HivisionIDPhotos 打包成 Windows 独立可执行程序。

## 📋 前置要求

- **操作系统**: Windows 10 / Windows 11
- **Python**: 3.10 或 3.11（推荐 3.10，兼容性最好）
- **内存**: 建议 8GB 以上
- **磁盘**: 打包过程需要约 5GB 临时空间

## 🚀 快速开始（推荐）

### 方法一：使用批处理脚本（最简单）

```bash
# 1. 克隆或下载项目到本地
git clone https://github.com/Zeyi-Lin/HivisionIDPhotos.git
cd HivisionIDPhotos

# 2. 安装项目依赖
pip install -r requirements.txt

# 3. 下载模型文件
python scripts/download_model.py --models all

# 4. 双击运行批处理脚本
build-windows.bat

# 或在命令行执行
.\build-windows.bat
```

### 方法二：手动打包

```bash
# 1. 安装打包工具
pip install pyinstaller

# 2. 清理旧构建
rmdir /s /q build dist

# 3. 执行打包
pyinstaller app.spec
```

## 📦 打包输出

打包完成后，可执行文件位于：
```
dist\HivisionIDPhotos.exe
```

**文件大小**: 约 200-300 MB（模型不打包进 exe，首次运行自动下载）

## ✨ 智能模型管理

本打包方案采用「**代码内置 + 运行时下载模型**」的优化方案：

| 特性 | 说明 |
|------|------|
| 🚀 **启动速度** | 第二次及以后启动秒开（无需每次解压大文件） |
| 📦 **exe 体积** | ~250MB（不是 800MB） |
| 🔄 **首次运行** | 自动下载默认模型 hivision_modnet.onnx（25MB） |
| 💾 **缓存模型** | 下载后模型保存在程序目录，下次直接使用 |

> **原理**: PyInstaller 单文件模式每次启动都要解压全部打包内容。模型不打包进 exe，启动时从本地磁盘直接读取，大大提升启动速度。

## ⚙️ 配置说明

### 调整打包内容

编辑 `app.spec` 文件可以自定义打包配置：

#### 1. 只打包特定模型（减小体积）
```python
# 默认打包所有模型，如需只打包特定模型，修改 datas:
datas += [
    ('hivision/creator/weights/hivision_modnet.onnx', 'hivision/creator/weights'),
    # 只添加需要的模型文件
]
```

#### 2. 关闭控制台窗口
```python
# 将 console=True 改为 False 可以不显示控制台窗口
console=False,
```
> **注意**: 关闭控制台后无法查看日志信息，建议调试时保持开启。

#### 3. 添加程序图标
```python
# 准备 .ico 格式图标文件，然后取消注释:
icon='assets/icon.ico',
```

### 模型配置说明

打包时会自动包含以下模型文件：
- `hivision_modnet.onnx` (25MB) - 默认推荐
- `modnet_photographic_portrait_matting.onnx` (25MB)
- `rmbg-1.4.onnx` (176MB)
- `birefnet-v1-lite.onnx` (224MB)

> **提示**: 如只需最小体积，可只保留 `hivision_modnet.onnx`，修改 `app.spec` 中的 datas 配置。

## 🔧 常见问题

### Q1: 打包后运行报错 "找不到模型文件"

**A**: 确保打包前已下载模型文件到正确目录：
```bash
python scripts/download_model.py --models all
```

### Q2: 打包后的 exe 文件体积太大

**A**: 优化方案：
1. 只打包需要的模型
2. 使用 UPX 压缩（已在spec中启用）
3. 排除不需要的模块

### Q3: 运行时杀毒软件报毒

**A**: PyInstaller 打包的程序经常被误报，解决方案：
1. 添加到杀毒软件白名单
2. 使用代码签名证书签名（需要购买）

### Q4: 打包速度太慢

**A**: 
- 首次打包较慢是正常的（5-15分钟）
- 确保有足够的磁盘空间和内存
- 关闭实时杀毒扫描可加快速度

### Q5: 打包成功但运行闪退

**A**: 开启控制台查看错误信息：
1. 保持 `console=True`
2. 在 cmd 中运行 `HivisionIDPhotos.exe`
3. 查看具体错误信息

## 📝 分发包建议

### 创建发布包结构
```
HivisionIDPhotos-Windows/
├── HivisionIDPhotos.exe    # 主程序
├── README.txt               # 使用说明
└── 首次运行请先读我.txt
```

### README.txt 内容示例：
```
========================================
    HivisionIDPhotos - 证件照制作工具
========================================

使用方法：
1. 双击运行 HivisionIDPhotos.exe
2. 等待浏览器自动打开（或手动访问 http://127.0.0.1:7860）
3. 上传照片，选择尺寸和背景色
4. 下载生成的证件照

常见问题：
- 首次启动较慢，请耐心等待
- 如浏览器未自动打开，请手动访问上面的地址
- 关闭程序请直接关闭控制台窗口
```

## 🎯 替代打包方案

### 方案 1: 使用 Nuitka（更快，更小）
```bash
pip install nuitka
python -m nuitka --standalone --onefile app.py
```

### 方案 2: 创建便携绿色版
不打包成单文件，使用文件夹分发模式：
```bash
# app.spec 中改为不打包成单文件
# 参考 PyInstaller 文档配置 COLLECT 部分
```

### 方案 3: Inno Setup 安装包
创建专业的安装程序：
```
1. 下载 Inno Setup
2. 编写 .iss 脚本
3. 生成 setup.exe 安装包
```

## 📌 注意事项

1. **Python 版本**: 建议使用 Python 3.10，新版本可能有兼容性问题
2. **虚拟环境**: 推荐在虚拟环境中打包，避免无关依赖被打包
3. **杀毒软件**: 打包过程中建议临时关闭实时扫描
4. **测试**: 打包后务必在干净的 Windows 环境中测试运行

## 📞 获取帮助

如遇打包问题：
1. 查看 PyInstaller 官方文档
2. 在项目 GitHub 提交 Issue
3. 参考社区项目：[HivisionIDPhotos-windows-GUI](https://github.com/zhaoyun0071/HivisionIDPhotos-windows-GUI)
