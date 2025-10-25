# MCP Bridge Server 打包指南

## 打包工具选择

推荐使用 **PyInstaller**，它支持将 Python 应用打包成独立的可执行文件。

## 环境准备

```bash
# 安装 PyInstaller
pip install pyinstaller

# 如果需要优化打包大小，安装 UPX
# Windows: 从 https://github.com/upx/upx/releases 下载
# Linux: sudo apt-get install upx
# Mac: brew install upx
```

## 打包配置文件

使用提供的 `mcp_bridge.spec` 配置文件进行打包。

### 基本打包命令

```bash
# 单文件打包（推荐用于分发）
pyinstaller --onefile --name mcp-bridge-server utils/mcp_bridge.py

# 使用 spec 文件打包（包含所有优化）
pyinstaller mcp_bridge.spec
```

### 高级打包选项

```bash
# Windows - 无控制台窗口（不推荐，因为需要看日志）
pyinstaller --onefile --noconsole --name mcp-bridge-server utils/mcp_bridge.py

# Windows - 带图标
pyinstaller --onefile --icon=icon.ico --name mcp-bridge-server utils/mcp_bridge.py

# 压缩可执行文件（需要 UPX）
pyinstaller --onefile --upx-dir=/path/to/upx --name mcp-bridge-server utils/mcp_bridge.py
```

## 多平台打包

### Windows

```bash
# 在 Windows 上打包
pyinstaller mcp_bridge.spec

# 输出: dist/mcp-bridge-server.exe
```

建议的文件名：
- `mcp-bridge-server-win-x64.exe` (64位)
- `mcp-bridge-server-win-x86.exe` (32位)

### Linux

```bash
# 在 Linux 上打包
pyinstaller mcp_bridge.spec

# 输出: dist/mcp-bridge-server
# 赋予执行权限
chmod +x dist/mcp-bridge-server
```

建议的文件名：
- `mcp-bridge-server-linux-x64`
- `mcp-bridge-server-linux-arm64`

### macOS

```bash
# 在 macOS 上打包
pyinstaller mcp_bridge.spec

# 输出: dist/mcp-bridge-server
chmod +x dist/mcp-bridge-server
```

建议的文件名：
- `mcp-bridge-server-macos-x64`
- `mcp-bridge-server-macos-arm64` (Apple Silicon)

## 打包注意事项

### 1. 隐藏导入

某些库可能需要显式声明：

```python
# 在 spec 文件中添加
hiddenimports=[
    'mcp',
    'mcp.client.stdio',
    'mcp.client.sse',
    'fastapi',
    'uvicorn',
    'pydantic',
]
```

### 2. 数据文件

如果有额外的资源文件：

```python
# 在 spec 文件中添加
datas=[
    ('README.md', '.'),
    ('docs', 'docs'),
],
```

### 3. 排除不需要的模块

减小文件大小：

```python
excludes=[
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'PIL',
    'PyQt5',
]
```

### 4. Windows 无控制台问题

**不要使用 `--noconsole`**，因为：
- 用户需要看到服务运行日志
- 端口检测需要交互式输入
- 调试时需要错误信息

如果确实需要无控制台版本，可以提供两个版本：
- `mcp-bridge-server.exe` - 控制台版本（推荐）
- `mcp-bridge-server-silent.exe` - 无控制台版本（仅用于服务模式）

## 测试打包后的程序

### 基本功能测试

```bash
# 1. 测试默认启动
./dist/mcp-bridge-server

# 2. 测试端口参数
./dist/mcp-bridge-server --port 8080

# 3. 测试帮助信息
./dist/mcp-bridge-server --help

# 4. 测试自动处理端口
./dist/mcp-bridge-server --auto-kill-port
```

### 完整测试清单

- [ ] 程序能正常启动
- [ ] 配置文件自动创建在正确位置
- [ ] 端口检测功能正常
- [ ] 可以加载 MCP 服务
- [ ] API 接口正常响应
- [ ] 重启服务功能正常
- [ ] 关闭服务功能正常
- [ ] Ctrl+C 能正常退出
- [ ] 文件大小合理（< 100MB）

## 优化打包大小

### 1. 使用虚拟环境

```bash
# 创建干净的虚拟环境
python -m venv venv_build
source venv_build/bin/activate  # Linux/Mac
venv_build\Scripts\activate     # Windows

# 只安装必要的依赖
pip install -r requirements.txt
pip install pyinstaller

# 打包
pyinstaller mcp_bridge.spec
```

### 2. 使用 UPX 压缩

```bash
# 自动使用 UPX（如果已安装）
pyinstaller --upx-dir=/usr/bin mcp_bridge.spec
```

### 3. 排除调试信息

```bash
pyinstaller --strip mcp_bridge.spec  # Linux/Mac
```

## CI/CD 自动打包

### GitHub Actions 示例

创建 `.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build
        run: pyinstaller mcp_bridge.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: mcp-bridge-server-win-x64
          path: dist/mcp-bridge-server.exe

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build
        run: pyinstaller mcp_bridge.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: mcp-bridge-server-linux-x64
          path: dist/mcp-bridge-server

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build
        run: pyinstaller mcp_bridge.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: mcp-bridge-server-macos-x64
          path: dist/mcp-bridge-server
```

## 发布建议

### 1. 版本命名

```
mcp-bridge-server-{version}-{platform}-{arch}.{ext}

示例:
- mcp-bridge-server-v1.0.0-win-x64.exe
- mcp-bridge-server-v1.0.0-linux-x64
- mcp-bridge-server-v1.0.0-macos-arm64
```

### 2. 发布内容

每个 Release 应包含：
- Windows 可执行文件（.exe）
- Linux 可执行文件
- macOS 可执行文件
- 源代码（自动）
- README.md
- CHANGELOG.md
- 使用文档链接

### 3. 文件校验

为每个文件生成 SHA256 校验和：

```bash
# Windows
certutil -hashfile mcp-bridge-server.exe SHA256

# Linux/Mac
sha256sum mcp-bridge-server
```

将校验和发布在 Release Notes 中。

## 常见问题

### Q: 打包后文件太大（>50MB）

**A**: 尝试以下方法：
1. 使用干净的虚拟环境
2. 排除不需要的模块
3. 使用 UPX 压缩
4. 检查是否包含了不必要的数据文件

### Q: 打包后无法运行

**A**: 检查：
1. 是否包含了所有必要的依赖
2. 查看 `build/mcp-bridge-server/warn-*.txt` 中的警告
3. 在目标系统上测试
4. 检查是否有隐藏导入未声明

### Q: 启动速度慢

**A**: 
1. 单文件模式会慢一些（需要解压）
2. 考虑使用目录模式（`--onedir`）
3. 首次运行会慢，后续会快

### Q: 杀毒软件误报

**A**: 
1. 使用代码签名证书签名可执行文件
2. 提交样本到杀毒软件厂商
3. 在 README 中说明

## 最佳实践

1. **保持依赖最小化** - 只安装必要的包
2. **测试多个系统** - 在干净的系统上测试
3. **提供校验和** - 让用户验证文件完整性
4. **保留源码** - 始终提供源码版本
5. **文档完善** - 详细的安装和使用说明
6. **版本控制** - 使用语义化版本号
7. **自动化构建** - 使用 CI/CD

## 打包脚本示例

创建 `build.sh` (Linux/Mac) 或 `build.bat` (Windows):

```bash
#!/bin/bash
# build.sh

echo "=== MCP Bridge Server 打包脚本 ==="

# 清理旧文件
rm -rf build dist

# 打包
pyinstaller mcp_bridge.spec

# 重命名
VERSION="v1.0.0"
PLATFORM="linux-x64"
mv dist/mcp-bridge-server dist/mcp-bridge-server-${VERSION}-${PLATFORM}

# 生成校验和
cd dist
sha256sum mcp-bridge-server-${VERSION}-${PLATFORM} > SHA256SUMS.txt

echo "=== 打包完成 ==="
echo "输出文件: dist/mcp-bridge-server-${VERSION}-${PLATFORM}"
```

现在您可以轻松地将项目打包成独立的可执行文件了！🚀
