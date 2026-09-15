"""Extras tab and Windows File Explorer integration."""

import sys
from pathlib import Path
from tkinter import messagebox, ttk


class ExtrasTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        install_frame = ttk.LabelFrame(self, text="Install", padding=10)
        install_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        install_frame.columnconfigure(0, weight=1)
        self.install_file_explorer_button = ttk.Button(
            install_frame, text="Install in File Explorer", command=self.install_in_file_explorer,
        )
        self.install_file_explorer_button.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="w")
        ttk.Label(
            install_frame,
            text=('Adds "Open in YOLO Media Sorter" to File Explorer right-click menus for '
                  "folders, folder backgrounds, and drives."),
            wraplength=720,
        ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

    def install_in_file_explorer(self):
        install()
        messagebox.showinfo(
            "File Explorer", "YOLO Media Sorter was installed in the File Explorer context menu.",
            parent=self,
        )


def install():
    """Register the current application for the current Windows user."""
    import winreg

    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()
        command = f'"{executable}"'
    else:
        executable = Path(sys.executable).with_name("pythonw.exe")
        code = f"import sys; sys.path.insert(0, {str(Path(__file__).resolve().parent.parent)!r}); from app.main import main; main()"
        command = f'"{executable}" -c "{code}"'

    for context, target in (
        (r"Directory\shell", "%1"),
        (r"Directory\Background\shell", "%V"),
        (r"Drive\shell", "%1"),
    ):
        menu_key = rf"Software\Classes\{context}\YOLO-media-sorter"
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, menu_key, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Open in YOLO Media Sorter")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{executable}",0')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, menu_key + r"\command", 0, winreg.KEY_SET_VALUE) as key:
            # A final dot keeps a drive's trailing backslash from escaping the closing quote.
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'{command} --source "{target}\\." --active-tab Scan')
