# -*- mode: python ; coding: utf-8 -*-
# FishWatch 빌드 설정 (PyInstaller). build_exe.bat 또는 GitHub Actions가 사용합니다.
# - Windows: dist/FishWatch.exe (파일 하나, 검은 실행 창 포함)
# - macOS  : dist/FishWatch.app (창 없는 앱. 화면의 [앱 종료]로 끕니다)
import sys

MAC = sys.platform == 'darwin'
VERSION = '1.1.4'

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[('rules.json', '.'), ('ui', 'ui'), ('sample_api', 'sample_api')],
    hiddenimports=['analyzer', 'collector', 'pipeline', 'report', 'paths', 'xlsx', '_strptime', 'plistlib',
                   'encodings.idna', 'encodings.utf_8_sig', 'encodings.cp949'] + ([] if MAC else ['winreg']),
    excludes=['tkinter', 'unittest', 'pydoc', 'test'],
    # True: 파이썬 모듈을 실행할 때 개별 파일로 풀어 둔다.
    # 점검 도중 exe 파일을 다시 열지 않으므로, 백신이 exe를 잠가도 PermissionError가 나지 않는다.
    noarchive=True,
)
pyz = PYZ(a.pure)

if MAC:
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name='FishWatch',
        console=False,
        icon='fishwatch.icns',
        upx=False, debug=False, strip=False,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name='FishWatch', upx=False, strip=False)
    app = BUNDLE(
        coll,
        name='FishWatch.app',
        icon='fishwatch.icns',
        bundle_identifier='kr.fishwatch.app',
        version=VERSION,
        info_plist={
            'CFBundleDisplayName': 'FishWatch',
            'CFBundleShortVersionString': VERSION,
            'CFBundleVersion': VERSION,
            'LSUIElement': True,          # 독(Dock)에 아이콘 없이 백그라운드로 돈다 (화면은 브라우저)
            'NSHumanReadableCopyright': '수산물 판매글 금어기·금지체장 점검 (개인 개발 도구)',
            'LSMinimumSystemVersion': '11.0',
        },
    )
else:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.datas, [],
        name='FishWatch',
        console=True,          # 검은 창을 닫으면 앱이 꺼진다
        icon='fishwatch.ico',
        version='version_info.txt',
        upx=False,             # 백신 오탐을 줄이려고 압축하지 않음
        debug=False, strip=False,
    )
