import tkinter as tk
from concurrent.futures import Future
from types import SimpleNamespace

from app.main import MainView
from app.scanner import MediaResult, ScanOptions


def test_context_menu_selects_clicked_file_and_tracks_move(tmp_path, monkeypatch):
    root = tk.Tk()
    root.geometry("1100x760")
    view = MainView(root)
    view.pack(fill="both", expand=True)
    view.options = ScanOptions(tmp_path)
    view.operation = "move"
    view.future = Future()
    view.future.set_result(1)
    source = tmp_path / "sample.png"
    destination = tmp_path / "model-label" / source.name
    predictions = [
        {"label": "model-label", "confidence": 0.9},
        {"label": "second-label", "confidence": 0.8},
        {"label": "second-label", "confidence": 0.7},
        {"label": "below-threshold", "confidence": 0.1},
    ]
    result = MediaResult(source, "model-label", 0.9, predictions, destination, False, None)
    view.emit("item", result)
    view.poll()
    root.update()
    assert not view.tree.item(str(source), "open")
    view.set_preview_expanded(True)
    assert view.tree.item(str(source), "open")
    view.refresh_results()
    assert view.tree.item(str(source), "open")
    view.set_preview_expanded(False)
    assert not view.tree.item(str(source), "open")
    matches = view.tree.get_children(str(source))
    assert len(matches) == 4
    assert int(view.tree.set(str(source), "count")) == 4
    assert [int(view.tree.set(row, "count")) for row in matches] == [1, 2, 2, 1]
    assert tuple(view.tree["columns"])[1:3] == ("label", "count")
    assert [view.tree.set(row, "label") for row in matches] == ["model-label", "second-label", "second-label", "below-threshold"]
    assert [float(view.tree.set(row, "confidence")) for row in matches] == [0.9, 0.8, 0.7, 0.1]
    opened = []
    monkeypatch.setattr("app.main.os.startfile", opened.append)
    monkeypatch.setattr(view.result_menu, "tk_popup", lambda *_: None)
    _, y, _, height = view.tree.bbox(str(source))
    view.show_result_menu(SimpleNamespace(y=y + height // 2, x_root=100, y_root=100))
    assert view.tree.selection() == (str(source),)
    view.result_menu.invoke(0)
    view.result_menu.invoke(1)
    assert opened == [source, source.parent]
    view.emit("moved", result)
    view.poll()
    view.result_menu.invoke(0)
    view.result_menu.invoke(1)
    assert opened[2:] == [destination, destination.parent]
    view.tree.selection_set(matches[1])
    view.result_menu.invoke(0)
    view.result_menu.invoke(1)
    assert opened[4:] == [destination, destination.parent]
    assert not hasattr(view, "destination")
    view.move_confidence.set(0.75)
    assert int(view.tree.set(str(source), "count")) == 4
    assert [int(view.tree.set(row, "count")) for row in view.tree.get_children(str(source))] == [1, 2, 2, 1]
    view.close()
