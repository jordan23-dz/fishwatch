# -*- mode: python ; coding: utf-8 -*-
# FishWatch.exe 빌드 설정 (PyInstaller). build_exe.bat 또는 GitHub Actions가 사용합니다.
a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[('rules.json', '.'), ('ui', 'ui'), ('sample_api', 'sample_api')],
    hiddenimports=['analyzer', 'collector', 'pipeline', 'report', 'paths'],
    excludes=['tkinter', 'unittest', 'pydoc', 'test'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FishWatch',
    console=True,          # 검은 창을 닫으면 앱이 꺼진다
    icon='fishwatch.ico',
    version='version_info.txt',
    upx=False,             # 백신 오탐을 줄이려고 압축하지 않음
    debug=False,
    strip=False,
)
