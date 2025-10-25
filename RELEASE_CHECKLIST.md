# 发布前检查清单

## 代码准备

- [ ] 更新 `version.py` 中的版本号
- [ ] 更新 `CHANGELOG.md` (如果有)
- [ ] 确保所有测试通过
- [ ] 检查代码中没有调试语句
- [ ] 更新文档中的版本号引用

## 打包准备

### 环境准备
- [ ] 创建干净的虚拟环境
  ```bash
  python -m venv venv_build
  source venv_build/bin/activate  # Linux/Mac
  venv_build\Scripts\activate     # Windows
  ```

- [ ] 安装依赖
  ```bash
  pip install -r requirements.txt
  pip install pyinstaller
  ```

### Windows 打包
- [ ] 在 Windows 系统上运行打包
  ```bash
  build.bat
  # 或
  pyinstaller mcp_bridge.spec
  ```

- [ ] 测试打包后的程序
  ```bash
  dist\mcp-bridge-server.exe --help
  dist\mcp-bridge-server.exe --version
  dist\mcp-bridge-server.exe --port 3849
  ```

- [ ] 重命名为发布名称
  ```
  mcp-bridge-server-v1.0.0-win-x64.exe
  ```

- [ ] 生成 SHA256 校验和
  ```bash
  certutil -hashfile dist\mcp-bridge-server-v1.0.0-win-x64.exe SHA256
  ```

### Linux 打包
- [ ] 在 Linux 系统上运行打包
  ```bash
  ./build.sh
  # 或
  pyinstaller mcp_bridge.spec
  ```

- [ ] 测试打包后的程序
  ```bash
  ./dist/mcp-bridge-server --help
  ./dist/mcp-bridge-server --version
  ./dist/mcp-bridge-server --port 3849
  ```

- [ ] 重命名为发布名称
  ```
  mcp-bridge-server-v1.0.0-linux-x64
  ```

- [ ] 生成 SHA256 校验和
  ```bash
  sha256sum dist/mcp-bridge-server-v1.0.0-linux-x64 > SHA256SUMS.txt
  ```

### macOS 打包
- [ ] 在 macOS 系统上运行打包
  ```bash
  ./build.sh
  # 或
  pyinstaller mcp_bridge.spec
  ```

- [ ] 测试打包后的程序
  ```bash
  ./dist/mcp-bridge-server --help
  ./dist/mcp-bridge-server --version
  ./dist/mcp-bridge-server --port 3849
  ```

- [ ] 重命名为发布名称
  ```
  mcp-bridge-server-v1.0.0-macos-x64
  mcp-bridge-server-v1.0.0-macos-arm64  # Apple Silicon
  ```

- [ ] 生成 SHA256 校验和
  ```bash
  sha256sum dist/mcp-bridge-server-v1.0.0-macos-* > SHA256SUMS.txt
  ```

## 功能测试

### 基本功能
- [ ] 程序启动正常
- [ ] 配置文件自动创建
- [ ] 端口检测功能正常
- [ ] 可以选择结束占用进程
- [ ] 可以选择更换端口
- [ ] `--help` 显示正常
- [ ] `--version` 显示正确版本
- [ ] `--port` 参数工作正常
- [ ] `--auto-kill-port` 工作正常
- [ ] `--config` 参数工作正常

### API 功能
- [ ] `GET /health` 正常响应
- [ ] `GET /tools` 返回服务列表
- [ ] `GET /tools?serverName=xxx` 返回工具列表
- [ ] `POST /execute` 可以执行工具
- [ ] `POST /reload` 可以重载配置
- [ ] `POST /restart-server` 可以重启单个服务
- [ ] `POST /shutdown-server` 可以关闭单个服务
- [ ] `POST /reset-history` 重置历史

### 错误处理
- [ ] 端口被占用时提示正确
- [ ] 配置文件错误时有友好提示
- [ ] MCP 服务启动失败时有错误信息
- [ ] API 错误返回详细信息
- [ ] Ctrl+C 能正常退出

### 性能检查
- [ ] 启动时间 < 5秒
- [ ] 文件大小合理 (< 100MB)
- [ ] 内存占用正常 (< 200MB)
- [ ] CPU 使用率正常

## 文档检查

- [ ] README.md 内容完整
- [ ] 所有文档链接有效
- [ ] 示例代码可以运行
- [ ] 截图（如有）清晰
- [ ] 安装说明准确
- [ ] 使用说明详细

## 发布准备

### GitHub Release
- [ ] 创建新的 Git Tag
  ```bash
  git tag -a v1.0.0 -m "Release v1.0.0"
  git push origin v1.0.0
  ```

- [ ] 准备 Release Notes
  - 新功能列表
  - Bug 修复
  - 已知问题
  - 升级说明

- [ ] 上传文件
  - [ ] Windows 可执行文件
  - [ ] Linux 可执行文件
  - [ ] macOS 可执行文件
  - [ ] SHA256SUMS.txt
  - [ ] README.md (可选)

### Release Notes 模板

```markdown
## MCP Bridge Server v1.0.0

### 新功能
- ✨ 智能端口检测与自动处理
- ✨ 单独重启/关闭服务功能
- ✨ 支持命令行参数和环境变量
- ✨ 友好的启动脚本

### 改进
- 🐛 修复 cancel scope 错误
- 📚 完善文档和使用指南
- 🎨 改进用户交互体验

### 下载

| 平台 | 文件 | SHA256 |
|------|------|--------|
| Windows x64 | mcp-bridge-server-v1.0.0-win-x64.exe | xxx... |
| Linux x64 | mcp-bridge-server-v1.0.0-linux-x64 | xxx... |
| macOS x64 | mcp-bridge-server-v1.0.0-macos-x64 | xxx... |
| macOS ARM64 | mcp-bridge-server-v1.0.0-macos-arm64 | xxx... |

### 安装和使用

1. 下载对应平台的文件
2. 验证 SHA256 校验和
3. 运行程序
4. 按提示配置 MCP 服务

详细文档: [README.md](README.md)

### 已知问题
- 无

### 升级说明
- 首次发布，无需升级
```

## 发布后

- [ ] 验证 Release 页面显示正常
- [ ] 测试下载链接有效
- [ ] 在干净的系统上测试下载的文件
- [ ] 更新项目主页（如有）
- [ ] 发布公告（如需要）
- [ ] 收集用户反馈

## 持续维护

- [ ] 监控 Issues
- [ ] 回复用户问题
- [ ] 收集功能建议
- [ ] 规划下一版本
- [ ] 保持文档更新

---

**版本**: v1.0.0  
**日期**: 2025-10-25  
**发布者**: [您的名字]
