"""Explicit launch overrides; omitted arguments never replace saved values."""

import argparse


def build_parser():
    parser = argparse.ArgumentParser(prog="yolo-media-sorter", argument_default=argparse.SUPPRESS)
    for name in ("source", "model", "crop-model", "device", "window-geometry", "ultralytics-api-key", "huggingface-api-key"):
        parser.add_argument(f"--{name}")
    for name in ("scan-confidence", "move-confidence", "frame-percentage"):
        parser.add_argument(f"--{name}", type=float)
    for name in ("min-predictions", "max-predictions"):
        parser.add_argument(f"--{name}", type=int)
    for name in ("recursive", "videos"):
        parser.add_argument(f"--{name}", action=argparse.BooleanOptionalAction)
    parser.add_argument("--selected-labels", nargs="*")
    parser.add_argument("--active-tab", choices=("Scan", "Models", "Settings", "Extras"))
    return parser
