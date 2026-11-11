# -*- mode: python ; coding: utf-8 -*-
# FishWatch.exe 빌드 설정 (PyInstaller). build_exe.bat 또는 GitHub Actions가 사용합니다.
a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[('rules.json', '.'), ('ui', 'ui'), ('sample_api', 'sample_api')],
    hiddenimports=['analyzer', 'collector', 'pipeline', 'report', 'paths', '_strptime',
                   'encodings.idna', 'encodings.utf_8_sig', 'encodings.cp949', 'winreg'],
    excludes=['tkinter', 'unittest', 'pydoc', 'test'],
    # True: 파이썬 모듈을 실행할 때 임시 폴더에 개별 파일로 풀어 둔다.
    # 점검 도중 exe 파일을 다시 열지 않으므로, 백신이 exe를 잠가도 PermissionError가 나지 않는다.
    noarchive=True,
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
