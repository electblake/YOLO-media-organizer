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

from app.arguments import build_parser
from app.config import CONFIG_DIR, AppState, Settings
from app.organizer import move_media, plan_moves
from app.scanner import MODEL_PRESETS, ScanOptions, scan


class MainView(ttk.Frame):
    def __init__(self, parent, settings):
        super().__init__(parent, padding=16)
        self.settings = settings
        values = settings.values
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
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
        self.sort_columns = dict(values.sort_columns)
        self.column_titles = {}
        self.original_rows = {"": []}
        self.data_dir = settings.config_path.parent
        self.source = tk.StringVar(self, value=values.source)
        self.model = tk.StringVar(self, value=values.model)
        self.crop_model = tk.StringVar(self, value=values.crop_model)
        self.scan_confidence = tk.DoubleVar(self, value=values.scan_confidence)
        self.move_confidence = tk.DoubleVar(self, value=values.move_confidence)
        self.min_predictions = tk.IntVar(self, value=values.min_predictions)
        self.max_predictions = tk.IntVar(self, value=values.max_predictions)
        self.frame_percentage = tk.DoubleVar(self, value=values.frame_percentage)
        self.device = tk.StringVar(self, value=values.device)
        self.recursive = tk.BooleanVar(self, value=values.recursive)
        self.videos = tk.BooleanVar(self, value=values.videos)
        self.status = tk.StringVar(self, value="Choose a media folder. Destinations are model-label folders inside it.")
        self.inputs = []

        heading = ttk.Frame(self)
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(heading, text="YOLO Media Sorter", font=("Segoe UI", 20, "bold")).pack(anchor="w")

        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=1, column=0, sticky="nsew")
        self.scan_tab = ttk.Frame(self.tabs)
        self.scan_tab.columnconfigure(0, weight=1)
        self.scan_tab.rowconfigure(2, weight=1)
        self.settings_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.scan_tab, text="Scan")
        self.tabs.add(self.settings_tab, text="Settings")
        self.tabs.select({"Scan": self.scan_tab, "Settings": self.settings_tab}[values.active_tab])
        self.settings_tab.columnconfigure(0, weight=1)
        ttk.Label(self.settings_tab, text="User config path").grid(row=0, column=0, sticky="w")
        self.config_path_var = tk.StringVar(self, value=str(settings.config_path))
        ttk.Entry(self.settings_tab, textvariable=self.config_path_var, state="readonly").grid(row=1, column=0, sticky="ew", pady=(4, 16))
        self.ultralytics_api_key = tk.StringVar(self, value=values.ultralytics_api_key)
        self.huggingface_api_key = tk.StringVar(self, value=values.huggingface_api_key)
        self.environment_key_vars = {}
        for row, environment, title, variable in [
            (2, "ULTRALYTICS_API_KEY", "Ultralytics API key override (optional)", self.ultralytics_api_key),
            (6, "HF_TOKEN", "Hugging Face API key override (optional)", self.huggingface_api_key),
        ]:
            ttk.Label(self.settings_tab, text=environment + " (environment)").grid(row=row, column=0, sticky="w")
            self.environment_key_vars[environment] = tk.StringVar(self, value=settings.environment_keys[environment])
            ttk.Entry(self.settings_tab, textvariable=self.environment_key_vars[environment], state="readonly").grid(
                row=row + 1, column=0, sticky="ew", pady=(4, 8),
            )
            ttk.Label(self.settings_tab, text=title).grid(row=row + 2, column=0, sticky="w")
            ttk.Entry(self.settings_tab, textvariable=variable).grid(row=row + 3, column=0, sticky="ew", pady=(4, 16))
        self.settings_tab.rowconfigure(10, weight=1)
        self.save_settings_button = ttk.Button(self.settings_tab, text="Save settings", command=self.save_settings)
        self.save_settings_button.grid(row=11, column=0, sticky="w")

        form = ttk.LabelFrame(self.scan_tab, text="Scan with YOLO Model", padding=12)
        form.grid(row=0, column=0, sticky="ew")
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

        actions = ttk.Frame(self.scan_tab)
        actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        self.scan_button = ttk.Button(actions, text="Scan & preview", command=self.start_scan)
        self.scan_button.pack(side="left")
        self.move_button = ttk.Button(actions, text="Move classified media", command=self.start_move, state="disabled")
        self.move_button.pack(side="left", padx=8)
        self.stop_button = ttk.Button(actions, text="Stop after current file", command=self.stop.set, state="disabled")
        self.stop_button.pack(side="left")
        self.save_config_button = ttk.Button(actions, text="Save config", command=self.save_config)
        self.save_config_button.pack(side="left", padx=(12, 4))
        self.reset_config_button = ttk.Button(actions, text="Reset config", command=self.reset_config)
        self.reset_config_button.pack(side="left", padx=4)
        self.default_config_button = ttk.Button(actions, text="Set default config", command=self.set_default_config)
        self.default_config_button.pack(side="left", padx=4)
        ttk.Button(actions, text="Open media folder", command=lambda: os.startfile(self.source.get())).pack(side="right")

        label_panel = ttk.LabelFrame(self.scan_tab, text="organize", padding=8)
        label_panel.grid(row=1, column=0, sticky="ew", pady=8)
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
        search = ttk.Frame(label_panel)
        search.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text="Filter labels").grid(row=0, column=0, padx=(0, 8))
        self.label_filter = tk.StringVar(self)
        ttk.Entry(search, textvariable=self.label_filter).grid(row=0, column=1, sticky="ew")
        self.label_filter.trace_add("write", self.filter_labels)
        self.label_canvas = tk.Canvas(label_panel, height=64, highlightthickness=0)
        self.label_canvas.grid(row=2, column=0, sticky="ew")
        label_scroll = ttk.Scrollbar(label_panel, orient="vertical", command=self.label_canvas.yview)
        label_scroll.grid(row=2, column=1, sticky="ns")
        self.label_canvas.configure(yscrollcommand=label_scroll.set)
        self.label_frame = ttk.Frame(self.label_canvas)
        self.label_frame.columnconfigure(0, weight=1)
        self.label_window = self.label_canvas.create_window(0, 0, window=self.label_frame, anchor="nw")
        self.label_frame.bind("<Configure>", lambda _: self.label_canvas.configure(scrollregion=self.label_canvas.bbox("all")))
        self.label_canvas.bind("<Configure>", lambda event: self.label_canvas.itemconfigure(self.label_window, width=event.width))

        table = ttk.Frame(self.scan_tab)
        table.grid(row=2, column=0, sticky="nsew")
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
        footer = ttk.Frame(self.scan_tab)
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status).grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        for variable in [self.move_confidence, self.min_predictions, self.max_predictions]:
            variable.trace_add("write", self.refresh_results)
        self.update_sort_headings()

    def current_state(self):
        values = {name: getattr(self, name).get() for name in (
            "source", "model", "crop_model", "scan_confidence", "move_confidence", "min_predictions",
            "max_predictions", "frame_percentage", "device", "recursive", "videos",
        )}
        return AppState(
            **values, selected_labels=self.settings.values.selected_labels,
            sort_columns=self.sort_columns,
            expanded_rows=[row for row in self.tree.get_children() if self.tree.item(row, "open")],
            window_geometry=self.winfo_toplevel().geometry(),
            active_tab=self.tabs.tab(self.tabs.select(), "text"),
        )

    def save_config(self):
        self.settings.save_state(self.current_state())

    def reset_config(self):
        self.settings.reset_state()
        values = self.settings.values
        for name in ("source", "model", "crop_model", "scan_confidence", "move_confidence", "min_predictions",
                     "max_predictions", "frame_percentage", "device", "recursive", "videos"):
            getattr(self, name).set(getattr(values, name))
        for label, variable in self.label_vars.items():
            variable.set(label in values.selected_labels)
        self.sort_columns = dict(values.sort_columns)
        self.update_sort_headings()
        for row in self.tree.get_children():
            self.tree.item(row, open=row in values.expanded_rows)
        self.winfo_toplevel().geometry(values.window_geometry)
        self.tabs.select({"Scan": self.scan_tab, "Settings": self.settings_tab}[values.active_tab])
        self.refresh_results()

    def set_default_config(self):
        self.settings.set_default(self.current_state())

    def save_settings(self):
        self.settings.save_config(
            ultralytics_api_key=self.ultralytics_api_key.get(),
            huggingface_api_key=self.huggingface_api_key.get(),
        )

    def select_label(self, label):
        labels = set(self.settings.values.selected_labels)
        if self.label_vars[label].get():
            labels.add(label)
        else:
            labels.discard(label)
        self.settings.values.selected_labels = sorted(labels)
        self.refresh_results()

    def set_preview_expanded(self, expanded):
        for row in self.tree.get_children():
            self.tree.item(row, open=expanded)

    def refresh_results(self, *_):
        visible_labels = sorted({prediction["label"] for result in self.results for prediction in result.predictions})
        for label in visible_labels:
            if label not in self.label_vars:
                self.label_vars[label] = tk.BooleanVar(self, value=label in self.settings.values.selected_labels)
                self.label_checks[label] = ttk.Checkbutton(
                    self.label_frame, text=label, variable=self.label_vars[label], command=lambda label=label: self.select_label(label),
                )
        self.filter_labels()
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
                self.tree.insert("", "end", iid=row, open=row in self.settings.values.expanded_rows)
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

    def filter_labels(self, *_):
        query = self.label_filter.get().casefold()
        for check in self.label_checks.values():
            check.grid_remove()
        matches = [label for label in sorted(self.label_checks) if query in label.casefold()]
        for position, label in enumerate(matches):
            self.label_checks[label].grid(row=position, column=0, sticky="ew", pady=2)

    def toggle_sort(self, column):
        if column not in self.sort_columns:
            self.sort_columns[column] = False
        elif not self.sort_columns[column]:
            self.sort_columns[column] = True
        else:
            del self.sort_columns[column]
        self.update_sort_headings()
        self.sort_table()

    def update_sort_headings(self):
        for name, title in self.column_titles.items():
            self.tree.heading(name, text=title)
        for priority, (name, descending) in enumerate(self.sort_columns.items(), 1):
            arrow = "▼" if descending else "▲"
            self.tree.heading(name, text=f"{self.column_titles[name]} {arrow}{priority}")

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


def main(argv=None):
    arguments = vars(build_parser().parse_args(argv))
    settings = Settings(CONFIG_DIR, arguments)
    settings.apply_api_keys()
    root = tk.Tk()
    root.title("YOLO Media Sorter")
    root.geometry(settings.values.window_geometry)
    root.minsize(920, 620)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    view = MainView(root, settings)
    view.grid(row=0, column=0, sticky="nsew")

    root.protocol("WM_DELETE_WINDOW", view.close)
    root.mainloop()


if __name__ == "__main__":
    main()
