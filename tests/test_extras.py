import ctypes
import sys
import winreg
from unittest.mock import MagicMock

import pytest

from app.arguments import build_parser
from app.config import AppState, Settings
from app.extras import install


@pytest.mark.parametrize("frozen", [False, True])
def test_explorer_commands_preserve_folder_and_drive_paths(monkeypatch, frozen):
    monkeypatch.setattr(sys, "frozen", frozen, raising=False)
    create_key = MagicMock()
    set_value = MagicMock()
    monkeypatch.setattr(winreg, "CreateKeyEx", create_key)
    monkeypatch.setattr(winreg, "SetValueEx", set_value)
    install()
    assert len(create_key.call_args_list) == 6
    keys = [call.args[1] for call in create_key.call_args_list[::2]]
    assert keys == [
        r"Software\Classes\Directory\shell\YOLO-media-organizer",
        r"Software\Classes\Directory\Background\shell\YOLO-media-organizer",
        r"Software\Classes\Drive\shell\YOLO-media-organizer",
    ]
    parse_command = ctypes.windll.shell32.CommandLineToArgvW
    parse_command.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
    parse_command.restype = ctypes.POINTER(ctypes.c_wchar_p)
    ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    for call in set_value.call_args_list[2::3]:
        for folder in ["C:\\", "C:\\Media folder", "\\\\server\\share\\"]:
            command = call.args[4].replace("%1", folder).replace("%V", folder)
            count = ctypes.c_int()
            pointer = parse_command(command, ctypes.byref(count))
            arguments = list(pointer[:count.value])
            ctypes.windll.kernel32.LocalFree(pointer)
            options = vars(build_parser().parse_args(arguments[-4:]))
            assert options == {"source": folder + "\\.", "active_tab": "Scan"}
            if frozen:
                assert len(arguments) == 5
            else:
                assert arguments[1] == "-c"
                compile(arguments[2], "<explorer launcher>", "exec")


def test_explorer_launch_overrides_saved_extras_tab(tmp_path):
    AppState(active_tab="Extras").save(tmp_path / "state.json")
    assert Settings(tmp_path, {}).values.active_tab == "Extras"
    arguments = vars(build_parser().parse_args(["--source", "C:\\Media", "--active-tab", "Scan"]))
    settings = Settings(tmp_path, arguments)
    assert settings.values.active_tab == "Scan"
    assert settings.values.source == "C:\\Media"
