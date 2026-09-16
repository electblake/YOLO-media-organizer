import os
import platform
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo,
)

root = Path(SPECPATH).parent
project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
version = project["version"]
artifact = f"YOLO-media-organizer-{version}-windows-{platform.machine().lower()}-{os.environ['YOLO_BUILD_BACKEND']}"
version_tuple = tuple(int(part) for part in version.split(".")) + (0,)
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=version_tuple, prodvers=version_tuple, mask=0x3f, flags=0,
                      OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
    kids=[StringFileInfo([StringTable("040904B0", [
        StringStruct("CompanyName", "electblake"),
        StringStruct("FileDescription", "YOLO Media Organizer"),
        StringStruct("FileVersion", version),
        StringStruct("ProductVersion", version),
        StringStruct("ProductName", "YOLO Media Organizer"),
        StringStruct("OriginalFilename", artifact + ".exe"),
    ])]), VarFileInfo([VarStruct("Translation", [1033, 1200])])],
)
a = Analysis(
    [str(root / "app/__main__.py")], pathex=[str(root)],
    datas=[(str(root / "README.md"), "."), (str(root / "BUILD.md"), "."), (str(root / "Models.md"), "."),
           (str(root / "assets"), "assets"), (str(root / "CHANGELOG.md"), "."), (str(root / "pyproject.toml"), ".")]
          + copy_metadata("ultralytics"),
    binaries=[], hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[], noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=artifact, version=version_info,
          debug=False, strip=False, upx=False, console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=artifact)
