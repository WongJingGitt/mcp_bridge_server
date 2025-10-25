# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 分析所有依赖
a = Analysis(
    ['utils/mcp_bridge.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'mcp',
        'mcp.client.stdio',
        'mcp.client.sse',
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pydantic',
        'pydantic.deprecated.decorator',
        'starlette',
        'anyio',
        'h11',
        'click',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'scipy',
        'sympy',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 收集所有文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mcp-bridge-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保持控制台窗口，用于显示日志和交互
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',  # 如果有图标文件，取消注释
)

# macOS 特定配置（如果需要打包成 .app）
# app = BUNDLE(
#     exe,
#     name='MCP Bridge Server.app',
#     icon='icon.icns',
#     bundle_identifier='com.mcp.bridge.server',
# )
