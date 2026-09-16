"""Hover hints for Tk controls."""

import tkinter as tk
from tkinter import ttk


class ToolTip:
    def __init__(self, widgets, text):
        self.text = text
        self.window = None
        for widget in widgets:
            widget.bind("<Enter>", self.show, add="+")
            for event in ("<Leave>", "<ButtonPress>", "<Escape>", "<Unmap>", "<Destroy>"):
                widget.bind(event, self.hide, add="+")

    def show(self, event):
        self.hide()
        widget = event.widget
        self.window = tk.Toplevel(widget)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        ttk.Label(self.window, text=self.text, wraplength=360, justify="left", padding=8, relief="solid").pack()
        self.window.update_idletasks()
        x = min(widget.winfo_rootx(), widget.winfo_screenwidth() - self.window.winfo_reqwidth())
        y = min(widget.winfo_rooty() + widget.winfo_height() + 4, widget.winfo_screenheight() - self.window.winfo_reqheight())
        self.window.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.window.deiconify()

    def hide(self, event=None):
        if self.window is not None:
            self.window.destroy()
            self.window = None
