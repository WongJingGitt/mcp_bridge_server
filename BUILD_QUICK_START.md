# 快速打包指南

## 🚀 最简单的方式

### Windows
```bash
# 1. 双击运行
build.bat

# 2. 选择选项 3（使用 spec 文件打包）

# 3. 完成！可执行文件在 dist 目录
```

### Linux/Mac
```bash
# 1. 赋予执行权限（首次）
chmod +x build.sh

# 2. 运行打包脚本
./build.sh

# 3. 选择选项 3（使用 spec 文件打包）

# 4. 完成！可执行文件在 dist 目录
```

## 📦 打包前准备（推荐）

```bash
# 1. 创建干净的虚拟环境
python -m venv venv_build

# 2. 激活虚拟环境
# Windows:
venv_build\Scripts\activate
# Linux/Mac:
source venv_build/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 4. 打包
# Windows:
build.bat
# Linux/Mac:
./build.sh
```

## 🎯 一键命令

### 使用 spec 文件（推荐）
```bash
pyinstaller mcp_bridge.spec
```

### 单文件打包
```bash
# Windows
pyinstaller --onefile --name mcp-bridge-server utils\mcp_bridge.py

# Linux/Mac
pyinstaller --onefile --name mcp-bridge-server utils/mcp_bridge.py
```

## ✅ 测试打包结果

```bash
# Windows
dist\mcp-bridge-server.exe --version
dist\mcp-bridge-server.exe --help
dist\mcp-bridge-server.exe

# Linux/Mac
./dist/mcp-bridge-server --version
./dist/mcp-bridge-server --help
./dist/mcp-bridge-server
```

## 📝 发布准备

### 1. 重命名文件

```bash
# Windows x64
mcp-bridge-server-v1.0.0-win-x64.exe

# Linux x64
mcp-bridge-server-v1.0.0-linux-x64

# macOS x64
mcp-bridge-server-v1.0.0-macos-x64

# macOS ARM64 (Apple Silicon)
mcp-bridge-server-v1.0.0-macos-arm64
```

### 2. 生成校验和

```bash
# Windows
certutil -hashfile mcp-bridge-server-v1.0.0-win-x64.exe SHA256

# Linux/Mac
sha256sum mcp-bridge-server-v1.0.0-* > SHA256SUMS.txt
```

## 🔍 常见问题

### Q: 打包失败，提示找不到模块
**A**: 确保在虚拟环境中安装了所有依赖
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Q: 文件太大（>50MB）
**A**: 
1. 使用干净的虚拟环境
2. spec 文件中已排除不需要的模块
3. 可以使用 UPX 压缩

### Q: Windows 杀毒软件报毒
**A**: 
1. 这是正常现象（PyInstaller 打包的特性）
2. 添加到白名单
3. 或使用代码签名证书

### Q: 打包后运行报错
**A**: 
1. 检查 `build/mcp-bridge-server/warn-*.txt`
2. 确认所有依赖都在 spec 文件的 hiddenimports 中
3. 在干净系统上测试

## 📚 详细文档

完整打包指南请查看: [docs/PACKAGING_GUIDE.md](docs/PACKAGING_GUIDE.md)

## 🎉 完成

打包完成后：
1. 在 `dist` 目录找到可执行文件
2. 测试功能是否正常
3. 重命名为发布版本名称
4. 生成 SHA256 校验和
5. 准备发布到 GitHub Releases

---

**提示**: 首次打包建议查看 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) 确保所有步骤都完成。
