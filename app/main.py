"""Tkinter desktop application."""

import os
import queue
import tkinter as tk
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from tkinter import filedialog, ttk

from app.organizer import move_media, plan_moves
from app.paths import CONFIG_DIR
from app.scanner import MODEL_PRESETS, ScanOptions, scan


class MainView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=16)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.events = queue.SimpleQueue()
        self.stop = Event()
        self.results = []
        self.move_plan = []
        self.moved_results = {}
        self.label_vars = {}
        self.label_checks = {}
        self.busy = False
        self.operation = ""
        self.result_paths = {}
        self.sort_columns = {}
        self.column_titles = {}
        self.original_rows = {"": []}
        self.data_dir = CONFIG_DIR
        self.source = tk.StringVar(self)
        self.model = tk.StringVar(self, value="DhanushSGowda/yolov8n-gender-classification")
        self.crop_model = tk.StringVar(self)
        self.scan_confidence = tk.DoubleVar(self, value=0.25)
        self.move_confidence = tk.DoubleVar(self, value=0.5)
        self.min_predictions = tk.IntVar(self, value=1)
        self.max_predictions = tk.IntVar(self, value=-1)
        self.frame_percentage = tk.DoubleVar(self, value=50)
        self.device = tk.StringVar(self)
        self.recursive = tk.BooleanVar(self, value=True)
        self.videos = tk.BooleanVar(self, value=True)
        self.status = tk.StringVar(self, value="Choose a media folder. Destinations are model-label folders inside it.")
        self.inputs = []

        heading = ttk.Frame(self)
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(heading, text="YOLO Media Sorter", font=("Segoe UI", 20, "bold")).pack(anchor="w")

        form = ttk.LabelFrame(self, text="Scan with YOLO Model", padding=12)
        form.grid(row=1, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        for row, (title, variable, folder) in enumerate([
            ("Media folder", self.source, True),
            ("YOLO model", self.model, False),
            ("Crop detector (optional)", self.crop_model, False),
        ]):
            ttk.Label(form, text=title).grid(row=row, column=0, sticky="w", pady=4)
            if variable is self.model:
                entry = ttk.Combobox(form, textvariable=variable, values=tuple(MODEL_PRESETS), width=60)
            else:
                entry = ttk.Entry(form, textvariable=variable, width=60)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=4)
            button = ttk.Button(form, text="Browse…", command=lambda v=variable, f=folder: self.browse(v, f))
            button.grid(row=row, column=2)
            self.inputs.extend([entry, button])
        self.inputs[0].focus_set()
        controls = ttk.Frame(form)
        controls.grid(row=5, column=0, columnspan=3, sticky="ew", pady=6)
        ttk.Label(controls, text="Scan confidence").pack(side="left")
        scan_threshold = ttk.Spinbox(
            controls, from_=0, to=1, increment=0.05, textvariable=self.scan_confidence, width=6, state="readonly",
        )
        scan_threshold.pack(side="left", padx=(6, 18))
        ttk.Label(controls, text="Video position %").pack(side="left")
        frame = ttk.Spinbox(controls, from_=0, to=100, increment=1, textvariable=self.frame_percentage, width=6, state="readonly")
        frame.pack(side="left", padx=(6, 18))
        ttk.Label(controls, text="Device (blank = YOLO default)").pack(side="left")
        device = ttk.Entry(controls, textvariable=self.device, width=9)
        device.pack(side="left", padx=6)
        self.inputs.extend([scan_threshold, frame, device])
        toggles = ttk.Frame(form)
        toggles.grid(row=6, column=0, columnspan=3, sticky="w")
        for title, variable in [("Include subfolders", self.recursive), ("Include videos", self.videos)]:
            toggle = ttk.Checkbutton(toggles, text=title, variable=variable)
            toggle.pack(side="left", padx=(0, 18))
            self.inputs.append(toggle)
        ttk.Label(form, text="Scan confidence is model input. Changing it requires a new scan.").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        actions = ttk.Frame(self)
        actions.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        self.scan_button = ttk.Button(actions, text="Scan & preview", command=self.start_scan)
        self.scan_button.pack(side="left")
        self.move_button = ttk.Button(actions, text="Move classified media", command=self.start_move, state="disabled")
        self.move_button.pack(side="left", padx=8)
        self.stop_button = ttk.Button(actions, text="Stop after current file", command=self.stop.set, state="disabled")
        self.stop_button.pack(side="left")
        ttk.Button(actions, text="Open media folder", command=lambda: os.startfile(self.source.get())).pack(side="right")

        label_panel = ttk.LabelFrame(self, text="Organize configuration", padding=8)
        label_panel.grid(row=2, column=0, sticky="ew", pady=8)
        label_panel.columnconfigure(0, weight=1)
        filters = ttk.Frame(label_panel)
        filters.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(filters, text="Move confidence").pack(side="left")
        self.move_threshold = ttk.Spinbox(
            filters, from_=0, to=1, increment=0.05, textvariable=self.move_confidence, width=6, state="readonly",
        )
        self.move_threshold.pack(side="left", padx=(8, 16))
        ttk.Label(filters, text="Min. predictions").pack(side="left")
        self.min_count = ttk.Spinbox(
            filters, from_=1, to=2147483647, increment=1, textvariable=self.min_predictions, width=7, state="readonly",
        )
        self.min_count.pack(side="left", padx=(8, 16))
        ttk.Label(filters, text="Max. predictions (-1 = unlimited)").pack(side="left")
        self.max_count = ttk.Spinbox(
            filters, from_=-1, to=2147483647, increment=1, textvariable=self.max_predictions, width=7, state="readonly",
        )
        self.max_count.pack(side="left", padx=8)
        self.label_canvas = tk.Canvas(label_panel, height=64, highlightthickness=0)
        self.label_canvas.grid(row=1, column=0, sticky="ew")
        label_scroll = ttk.Scrollbar(label_panel, orient="vertical", command=self.label_canvas.yview)
        label_scroll.grid(row=1, column=1, sticky="ns")
        self.label_canvas.configure(yscrollcommand=label_scroll.set)
        self.label_frame = ttk.Frame(self.label_canvas)
        self.label_window = self.label_canvas.create_window(0, 0, window=self.label_frame, anchor="nw")
        self.label_frame.bind("<Configure>", lambda _: self.label_canvas.configure(scrollregion=self.label_canvas.bbox("all")))
        self.label_canvas.bind("<Configure>", lambda event: self.label_canvas.itemconfigure(self.label_window, width=event.width))

        table = ttk.Frame(self)
        table.grid(row=3, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(1, weight=1)
        preview_controls = ttk.Frame(table)
        preview_controls.grid(row=0, column=0, columnspan=2, sticky="e", pady=(0, 6))
        ttk.Button(preview_controls, text="Collapse all", command=lambda: self.set_preview_expanded(False)).pack(side="left", padx=(0, 6))
        ttk.Button(preview_controls, text="Expand all", command=lambda: self.set_preview_expanded(True)).pack(side="left")
        self.tree = ttk.Treeview(table, columns=("source", "label", "count", "confidence", "destination"), show="tree headings")
        self.tree.column("#0", width=36, minwidth=36, stretch=False)
        for name, title, width in [
            ("source", "original", 230), ("label", "labels", 120),
            ("count", "count", 115),
            ("confidence", "conf", 125), ("destination", "destination", 330),
        ]:
            self.column_titles[name] = title
            self.tree.heading(name, text=title, anchor="w", command=lambda column=name: self.toggle_sort(column))
            self.tree.column(name, width=width, minwidth=70)
        self.tree.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=2, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        self.result_menu = tk.Menu(self, tearoff=False)
        self.result_menu.add_command(label="Open file", command=self.open_result_file)
        self.result_menu.add_command(label="Open path", command=self.open_result_path)
        self.tree.bind("<Button-3>", self.show_result_menu)
        footer = ttk.Frame(self)
        footer.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status).grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        for variable in [self.move_confidence, self.min_predictions, self.max_predictions]:
            variable.trace_add("write", self.refresh_results)

    def set_preview_expanded(self, expanded):
        for row in self.tree.get_children():
            self.tree.item(row, open=expanded)

    def refresh_results(self, *_):
        visible_labels = sorted({prediction["label"] for result in self.results for prediction in result.predictions})
        for label in visible_labels:
            if label not in self.label_vars:
                self.label_vars[label] = tk.BooleanVar(self, value=False)
                self.label_checks[label] = ttk.Checkbutton(
                    self.label_frame, text=label, variable=self.label_vars[label], command=self.refresh_results,
                )
        for check in self.label_checks.values():
            check.grid_remove()
        for position, label in enumerate(visible_labels):
            self.label_checks[label].grid(row=position // 4, column=position % 4, sticky="w", padx=(0, 18), pady=2)
        selected = {label for label in visible_labels if self.label_vars[label].get()}
        self.move_plan = plan_moves(
            [result for result in self.results if result.source not in self.moved_results],
            self.options.source, selected, self.move_confidence.get(), self.min_predictions.get(), self.max_predictions.get(),
        ) if self.results else []
        planned = {result.source: result for result in self.move_plan}
        selection = self.tree.selection()
        self.original_rows = {"": []}
        for result in self.results:
            predictions = [(index, prediction) for index, prediction in enumerate(result.predictions)
                           if prediction["confidence"] >= self.move_confidence.get()]
            counts = Counter(prediction["label"] for _, prediction in predictions)
            row = str(result.source)
            self.original_rows[""].append(row)
            self.original_rows[row] = []
            destination = self.moved_results[result.source].destination if result.source in self.moved_results else (
                planned[result.source].destination if result.source in planned else None
            )
            self.result_paths[row] = self.moved_results[result.source].destination if result.source in self.moved_results else result.source
            if not self.tree.exists(row):
                self.tree.insert("", "end", iid=row, open=False)
            self.tree.item(row, values=(
                result.source.relative_to(self.options.source), "", counts.total(), "", destination if destination is not None else "",
            ))
            for child in self.tree.get_children(row):
                del self.result_paths[child]
            self.tree.delete(*self.tree.get_children(row))
            for index, prediction in predictions:
                child = f"{row}::match:{index}"
                self.result_paths[child] = self.result_paths[row]
                self.original_rows[row].append(child)
                self.tree.insert(row, "end", iid=child, values=(
                    "", prediction["label"], counts[prediction["label"]], prediction["confidence"], "",
                ))
        self.sort_table()
        self.tree.selection_set([row for row in selection if self.tree.exists(row)])
        self.move_button.state(["!disabled"] if self.results and not (self.busy and self.operation == "scan") else ["disabled"])

    def toggle_sort(self, column):
        if column not in self.sort_columns:
            self.sort_columns[column] = False
        elif not self.sort_columns[column]:
            self.sort_columns[column] = True
        else:
            del self.sort_columns[column]
        for name, title in self.column_titles.items():
            self.tree.heading(name, text=title)
        for priority, (name, descending) in enumerate(self.sort_columns.items(), 1):
            arrow = "▼" if descending else "▲"
            self.tree.heading(name, text=f"{self.column_titles[name]} {arrow}{priority}")
        self.sort_table()

    def sort_value(self, row, column):
        if column in {"label", "confidence"} and not self.tree.parent(row):
            return tuple(sorted(
                (self.sort_value(child, column) for child in self.tree.get_children(row)),
                reverse=self.sort_columns[column],
            ))
        value = self.tree.set(row, column)
        if value == "":
            return ()
        return (float(value),) if column in {"confidence", "count"} else (value.casefold(),)

    def sort_table(self):
        for parent, original in self.original_rows.items():
            rows = list(original)
            for column, descending in reversed(self.sort_columns.items()):
                rows.sort(key=lambda row, column=column: self.sort_value(row, column), reverse=descending)
            for position, row in enumerate(rows):
                self.tree.move(row, parent, position)

    def show_result_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.tree.focus(row)
            self.result_menu.tk_popup(event.x_root, event.y_root)
            self.result_menu.grab_release()
        else:
            self.result_menu.unpost()

    def open_result_file(self):
        os.startfile(self.result_paths[self.tree.selection()[0]])

    def open_result_path(self):
        os.startfile(self.result_paths[self.tree.selection()[0]].parent)

    def browse(self, variable, folder):
        selection = filedialog.askdirectory(parent=self) if folder else filedialog.askopenfilename(parent=self)
        if selection:
            variable.set(selection)

    def set_busy(self, busy):
        self.busy = busy
        for widget in self.inputs + [self.scan_button]:
            widget.state(["disabled"] if busy else ["!disabled"])
        self.stop_button.state(["!disabled"] if busy else ["disabled"])
        self.move_button.state(["!disabled"] if self.results and not (busy and self.operation == "scan") else ["disabled"])

    def start_scan(self):
        self.options = ScanOptions(
            source=Path(self.source.get()).resolve(),
            model=MODEL_PRESETS[self.model.get()] if self.model.get() in MODEL_PRESETS else self.model.get(),
            crop_model=self.crop_model.get(),
            scan_confidence=self.scan_confidence.get(),
            frame_percentage=self.frame_percentage.get(), device=self.device.get(),
            recursive=self.recursive.get(), include_videos=self.videos.get(),
        )
        self.results = []
        self.move_plan = []
        self.moved_results.clear()
        for check in self.label_checks.values():
            check.destroy()
        self.label_checks.clear()
        self.label_vars.clear()
        self.result_paths.clear()
        self.original_rows = {"": []}
        self.tree.delete(*self.tree.get_children())
        self.stop.clear()
        self.progress["value"] = 0
        self.operation = "scan"
        self.set_busy(True)
        self.future = self.executor.submit(scan, self.options, self.data_dir / "index.sqlite3", self.stop, self.emit)
        self.after(75, self.poll)

    def start_move(self):
        self.stop.clear()
        self.operation = "move"
        self.set_busy(True)
        self.progress.configure(value=0, maximum=len(self.move_plan))
        self.status.set("Moving original media")
        journal = self.data_dir / "moves" / (datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f") + ".csv")
        self.future = self.executor.submit(move_media, self.move_plan, journal, self.stop, self.emit)
        self.after(75, self.poll)

    def emit(self, kind, payload):
        self.events.put((kind, payload))

    def poll(self):
        rows_changed = False
        for _ in range(100):
            if self.events.empty():
                break
            kind, payload = self.events.get()
            if kind == "status":
                self.status.set(payload)
            elif kind == "total":
                self.progress["maximum"] = payload
            elif kind == "item":
                rows_changed = True
                self.results.append(payload)
                self.progress["value"] += 1
            elif kind == "moved":
                rows_changed = True
                self.moved_results[payload.source] = payload
                self.progress["value"] += 1
        if rows_changed:
            self.refresh_results()
        if not self.future.done() or not self.events.empty():
            self.after(75, self.poll)
            return
        self.set_busy(False)
        result = self.future.result()
        self.refresh_results()
        if self.operation == "scan":
            self.status.set(f"{'Stopped' if self.stop.is_set() else 'Scan complete'} · {len(self.results)} media")
        else:
            self.status.set(f"{'Stopped' if self.stop.is_set() else 'Complete'} · {result} files moved · Journal: {self.data_dir / 'moves'}")

    def close(self):
        self.stop.set()
        self.executor.shutdown(wait=False)
        self.winfo_toplevel().destroy()


def main():
    root = tk.Tk()
    root.title("YOLO Media Sorter")
    root.geometry("1100x760")
    root.minsize(920, 620)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    view = MainView(root)
    view.grid(row=0, column=0, sticky="nsew")
    root.protocol("WM_DELETE_WINDOW", view.close)
    root.mainloop()


if __name__ == "__main__":
    main()
