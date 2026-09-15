import tkinter as tk
from concurrent.futures import Future

from app.main import MainView
from app.scanner import MediaResult, ScanOptions


def test_column_cycles_priority_numeric_matches_and_live_results(tmp_path):
    root = tk.Tk()
    root.geometry("1100x760")
    view = MainView(root)
    view.pack(fill="both", expand=True)
    view.options = ScanOptions(tmp_path)
    view.move_confidence.set(0)
    view.operation = "scan"
    view.future = Future()
    view.future.set_result([])
    results = []
    for filename, label, scores in [
        ("z.png", "beta", [0.9, 0.00001]),
        ("b.png", "alpha", [0.8]),
        ("a.png", "alpha", [0.7]),
    ]:
        source = tmp_path / filename
        result = MediaResult(source, label, scores[0], [
            {"label": label, "confidence": score} for score in scores
        ], tmp_path / label / filename, False, None)
        results.append(result)
        view.emit("item", result)
    view.poll()
    root.update()
    original = tuple(str(result.source) for result in results)

    def click(column):
        root.tk.call(view.tree.heading(column, "command"))

    click("source")
    assert view.tree.get_children() == tuple(reversed(original))
    click("source")
    assert view.tree.get_children() == original
    click("source")
    assert view.tree.get_children() == original
    assert view.sort_columns == {}
    assert view.tree.heading("source", "text") == "original"

    click("label")
    assert view.tree.get_children() == (original[1], original[2], original[0])
    click("confidence")
    assert view.tree.get_children() == (original[2], original[1], original[0])
    assert view.tree.heading("confidence", "text").endswith("▲2")
    matches = view.tree.get_children(original[0])
    assert [float(view.tree.set(row, "confidence")) for row in matches] == [0.00001, 0.9]
    view.tree.selection_set(matches[0])
    click("confidence")
    assert view.tree.get_children() == (original[1], original[2], original[0])
    assert view.tree.selection() == (matches[0],)
    click("confidence")
    click("label")
    click("label")
    assert view.tree.get_children() == original
    assert [float(view.tree.set(row, "confidence")) for row in view.tree.get_children(original[0])] == [0.9, 0.00001]

    click("source")
    source = tmp_path / "aa.png"
    view.emit("item", MediaResult(source, None, None, [], None, False, None))
    view.poll()
    assert view.tree.get_children() == (original[2], str(source), original[1], original[0])
    click("source")
    click("source")
    assert view.tree.get_children() == (*original, str(source))
    view.emit("moved", results[1])
    view.poll()
    assert view.tree.get_children() == (*original, str(source))
    assert results[0].predictions[0]["confidence"] == 0.9
    many = tmp_path / "many.png"
    view.emit("item", MediaResult(many, None, None, [{"label": "beta", "confidence": 0.9}] * 10, None, False, None))
    view.poll()
    click("count")
    assert [int(view.tree.set(row, "count")) for row in view.tree.get_children()] == [0, 1, 1, 2, 10]
    click("count")
    assert [int(view.tree.set(row, "count")) for row in view.tree.get_children()] == [10, 2, 1, 1, 0]
    click("count")
    assert view.tree.get_children() == (*original, str(source), str(many))
    view.close()
