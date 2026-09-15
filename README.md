# YOLO Media Sorter

A Python/Tkinter desktop app that indexes images and video snapshots with Ultralytics YOLO, previews the predicted labels, and moves original media into label-named folders.

## Run

Install Python 3.12+ with Tkinter and [uv](https://docs.astral.sh/uv/), then:

```powershell
uv sync
uv run yolo-media-sorter
```

## Configuration and saved state

`app/config.py` defines the Pydantic models and `PlatformDirs("YOLO-media-sorter", appauthor=False).user_config_path`. On Windows this is `%LOCALAPPDATA%\YOLO-media-sorter`.

- `config.json` contains user defaults and explicitly saved API key overrides. Built-in defaults are used before a user config has been saved.
- `state.json` stores scan and organize settings, selected labels, sorting, expanded preview rows, window geometry, both divider positions, and the active tab only when **Save config** is clicked. Changing controls, switching tabs, resizing, and closing the app do not save anything.
- Startup precedence is **defaults < user config < saved state < explicitly supplied app arguments**. Omitted arguments have no defaults that overwrite restored values. Launch arguments are written to state only when **Save config** is clicked.

Like Spectra's **Reset Default**, **Reset config** restores built-in defaults in the current UI without changing either saved file. Click **Save config** to persist the reset; closing without saving retains the previously saved configuration. API key settings are unaffected. **Set default config** saves the current Sort Media values as user defaults and clears older state overrides. These buttons are in the Scan tab’s bottom controls. API key inputs are still saved separately with **Save settings**.

For example:

```powershell
uv run yolo-media-sorter --source 'D:\Media' --model yolov8n-cls --move-confidence 0.7 --no-videos
uv run yolo-media-sorter --help
```

`--selected-labels label-a label-b` overrides saved label selections; `--selected-labels` clears them for that launch. Scan results remain in the inference index; a new scan repopulates the preview using cached predictions. Saved label selections and row expansion are restored when those labels and files appear.

The **Settings** tab shows the current config file path and the `ULTRALYTICS_API_KEY` and `HF_TOKEN` environment values. Optional API key overrides are saved to `config.json` only when **Save settings** is pressed, and apply to subsequent model downloads. An empty override uses the environment value. Environment values are never copied into either JSON file. `--ultralytics-api-key` and `--huggingface-api-key` can also supply explicit launch overrides.

## Layout

Drag the main divider to resize the configuration tabs on the left and results on the right. In Sort Media, drag the horizontal divider to give more space to scan settings or the organize label list. Scan settings scroll vertically when they exceed the available height. Results, scan/move/stop actions, configuration buttons, and progress remain visible on every tab.

**Save config** saves both divider positions. **Reset config** restores their built-in positions without saving; **Set default config** includes them in your user defaults.

## Workflow

1. Select the media folder. Destination folders are derived automatically from the loaded model’s predicted labels inside this folder.
2. Choose a model in **Models > YOLO Classify & Detect > model**, type any compatible Ultralytics model reference, or browse for a local model file. The listed models are presets, not restrictions on classification categories. `hf://owner/repository/filename` downloads a specific Hugging Face weight file.
3. Set **Scan confidence** (model input, default 0.25) and the video frame position (50% by default). Subfolders and videos are included by default.
4. Click **Preview sorting**. File rows start collapsed. Expand a row to see every returned prediction, or use **Expand all** and **Collapse all** above the table. Each prediction retains its model label and raw output confidence, including repeated predictions.
5. In **Organize configuration**, check labels to move and set **Move confidence**, **Min. predictions**, and **Max. predictions**. Labels start unchecked. Minimum defaults to 1 and cannot be 0; maximum defaults to -1, meaning unlimited.
6. Click **Sort media** to move those files. Scanning alone never moves media.

Right-click a preview row for **Open file** or **Open path** (the containing folder). These actions track the current file location after a move.

Use **Extras > Install > Install in File Explorer** to add **Open in YOLO Media Sorter** to the current Windows user's right-click menus for folders, folder backgrounds, and drives. The menu opens the Sort Media tab with that folder selected as the media source.

**Prediction count**, immediately after **Predicted label**, shows total returned predictions on each file row and the count for that label on each match row. These preview counts retain repeated predictions and sort numerically. Organize filters do not hide raw scan predictions or change these counts. They do not imply a count of people or objects.

```text
input/holiday/IMG_0123.jpg  ->  input/22+/holiday/IMG_0123.jpg
input/clip.mp4             ->  input/22+/clip.mp4
```

One model is used per scan. For each file, organize rules count predictions whose labels are checked and whose confidence is at least **Move confidence**. The file qualifies when this count is at least the minimum and no greater than the maximum, with -1 disabling the maximum. Zero matches never qualifies. If several checked labels qualify, the highest-confidence checked match determines its folder; an unchecked label never determines the move. For detection models, matches include all returned objects; for a crop pipeline, all detected crops. Labels are read from the loaded model's `names` mapping through its prediction results. All returned predictions are stored in the index.

### Input and output confidence

**Scan confidence** belongs to **Scan with YOLO Classification Model** and is passed to Ultralytics as the prediction `conf` input, including the optional crop detector. Its effect depends on the model task: detection uses it to filter boxes; classification returns class probabilities. Changing it requires a new scan and uses a separate inference-cache signature. **Move confidence** belongs to Organize configuration and defaults to 0.5. It is compared only with stored model-output scores when planning moves. Changing move confidence, count bounds, or checked labels updates the move plan without inference and without removing predictions from the preview. Lowering move confidence cannot recover detections already discarded at scan time.

Original filenames and relative subfolders are retained. Characters in labels that cannot be used safely in folder names are percent-encoded. A move uses exclusive destination creation, copies the bytes and file metadata, then deletes the original. An existing destination fails naturally without overwriting it. Moves also work across volumes. There is no automatic retry, rollback, skip-on-error, or filename substitution; a failed copy may leave a partial destination while retaining the source. Completed moves are recorded in a CSV journal.

Click a preview column heading to cycle ascending, descending, then off. Multiple columns sort in selection order; heading arrows show direction and priority. Matches stay under their files. Label and confidence sorts order file groups by their sorted match values and also sort the match rows. Clearing all sort columns restores the original scan order.

## Models

The app calls `YOLO(...).predict(...)` and uses the standard Ultralytics preprocessing and results. It does not implement custom image resizing, feature extraction, embeddings, similarity, clustering, comparisons, or duplicate detection.

Classification and detection models share the **model** dropdown in **Models > YOLO Classify & Detect**. Each detection contributes its model-provided label and confidence to the same preview and organize workflow; box coordinates are discarded. Repeated labels remain separate predictions and count separately. The selected model and scan settings are part of the cache key.

Ultralytics Platform models accept `ul://owner/project/model` or a platform model-page URL in the model field. Downloads use the native Ultralytics loader and are stored under the app's `models/platform` directory. Set `ULTRALYTICS_API_KEY` using a key from [Platform settings](https://platform.ultralytics.com/settings) for API downloads. Downloaded `.pt` files can also be selected with Browse.

| Preset | Source | Output |
| --- | --- | --- |
| rpi5/person-detection/yolov8nbest | [Ultralytics Platform](https://platform.ultralytics.com/rpi5/person-detection/yolov8nbest) | Model-provided detection labels |
| leeyunjai/yolo11-ko-face-emotion-cls | [Model source](https://huggingface.co/leeyunjai/yolo11-ko-face-emotion-cls) | Model-provided labels from `yolo11x-face-emotion.pt` |
| NguyenToanLe/Age-Gender-Detection-YOLO / age, gender | [Model sources](https://github.com/NguyenToanLe/Age-Gender-Detection-YOLO/tree/main/models) | Separate `age.pt` and `gender.pt` checkpoints; labels read from each model |
| DhanushSGowda/yolov8n-gender-classification | [Model source](https://huggingface.co/DhanushSGowda/yolov8n-gender-classification) | Whole-image class probabilities |
| AdamCodd/yolo11n-face-age | [Model source](https://huggingface.co/AdamCodd/yolo11n-face-age) | Face boxes with age-range labels |
| MnLgt/yolo-human-parse | [Model source](https://huggingface.co/MnLgt/yolo-human-parse) | Body-part and object labels from segmentation detections |
| yolo26n-cls | [Ultralytics](https://platform.ultralytics.com/ultralytics/yolo26/yolo26n-cls) | Whole-image class probabilities; Ultralytics downloads `yolo26n-cls.pt` by name |
| yolo11n-cls | [Ultralytics](https://platform.ultralytics.com/ultralytics/yolo11/yolo11n-cls) | Whole-image class probabilities; Ultralytics downloads `yolo11n-cls.pt` by name |
| yolov8n-cls | [Ultralytics](https://platform.ultralytics.com/ultralytics/yolov8/yolov8n-cls) | Whole-image class probabilities; Ultralytics downloads `yolov8n-cls.pt` by name |
| dgyawa/yolo12n-cls-imagenet1k | [Model source](https://huggingface.co/dgyawa/yolo12n-cls-imagenet1k) | Whole-image class probabilities from `yolo12n-cls.pt` |
| Anzhcs Breast size det cls v8 640 y11m | [Model source](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhcs%20Breast%20size%20det%20cls%20v8%20640%20y11m.pt) | Detection boxes with model-provided labels |
| yolov8n-oiv7, yolov8l-oiv7, yolov8x-oiv7 | [Ultralytics](https://docs.ultralytics.com/datasets/detect/open-images-v7) | Open Images V7 detection labels; Ultralytics downloads weights by name |
| yolov8s-oiv7, yolov8m-oiv7 | [Model source](https://huggingface.co/shirabendor/YOLOV8-oiv7) | Open Images V7 detection labels |
| booru_yolo variants | [Model sources](https://github.com/aperveyev/booru_yolo/tree/main/models) | Detection boxes with model-provided labels |

The booru_yolo dropdown variants are `yolov11m_aa22`, `yolov11m_mm07`, `yolov11m_pp15`, `yolov8m_as02`, `yolov8m_as03`, `yolov8m_pp14`, `yolov8n_as01`, `yolov8s_aa06`, `yolov8s_aa09`, `yolov8s_aa10`, `yolov8s_aa11`, `yolov8s_pp09`, and `yolov8s_pp12`. ZIP-packaged checkpoints are extracted inside the app's model directory on first use.

Local compatible classification, detection, segmentation, pose, and oriented-box models can supply labels through `probs`, `boxes`, or `obb`. Exported formats need their Ultralytics runtime dependencies installed; unsupported models fail at their native operation. The app does not invent labels for models without class outputs. Device selection is passed to Ultralytics when set (e.g. `cpu` or `0`); blank uses its default. Model weights download on first use.

For classifiers trained on cropped faces, set **Crop detector** to a face detection model. The app runs that detector, crops each returned box, then passes each crop through the chosen model's standard prediction pipeline. With no detected faces, the file remains unclassified. Leave the crop detector blank for whole-image inference or the face-age detection preset. This follows the detector-to-classifier approach in [Age-Gender-Detection-YOLO](https://github.com/NguyenToanLe/Age-Gender-Detection-YOLO); that project's weights can be selected locally.

The face-age model is published under CC-BY-NC-4.0 for non-commercial research. Model licences are separate from application code and Ultralytics licensing.

## Scanning and indexing

The technology and snapshot workflow follow [Spectra](https://github.com/electblake/Spectra): Python, Tkinter/ttk, Pillow, OpenCV, and a background worker. This is an independent implementation of the classification workflow; no comparison or similarity code is included.

- Each video contributes one frame at `round((frame_count - 1) * percentage / 100)`, using OpenCV's FFmpeg backend. The frame is processed through the same image pipeline; the original video is moved.
- Images are oriented using EXIF and converted to RGB. GIFs use their first image frame.
- Supported images: JPG/JPEG, PNG, BMP, GIF, TIF/TIFF, WEBP. Videos: MP4, AVI, WMV, MPEG/MPG, MOV, M4V, MKV, WEBM; decoding depends on OpenCV's codecs.
- Top-level folders matching the loaded model’s label names are excluded from scanning so organized files are not nested into label folders again. Symbolic links are not traversed.
- A SQLite index reuses predictions when absolute path, file size, modification time, model weights metadata, inference settings, and Ultralytics version match. No image hashes or visual features are calculated. Content changes that deliberately preserve both size and timestamp require deleting the index to force a fresh scan.
- App-managed files use `PlatformDirs("YOLO-media-sorter", appauthor=False).user_config_path` (`%LOCALAPPDATA%\YOLO-media-sorter` on Windows). This includes the SQLite index, CSV move journals, models, library settings, and runtime caches. Media remains in the selected media folder and its label subfolders.
- **Stop after current file** preserves completed index entries or moves. A later scan resumes through cached predictions. Changes to the model, source, or scan confidence require a new scan. Move confidence, count bounds, and label selections do not.

Leave source files unchanged between preview and move. Keep the launch terminal available: dependency, model, decoding, and filesystem failures propagate there without application recovery handlers.

### App storage

`platformdirs` is a required project dependency. All paths below are relative to its app configuration directory:

| Content | Location |
| --- | --- |
| Scan index | `index.sqlite3` |
| Move journals | `moves/` |
| Named Ultralytics model downloads | `models/ultralytics/` |
| Hugging Face model cache | `models/huggingface/` |
| Imported local models | `models/local/` |
| Model URL downloads | `models/urls/` |
| Ultralytics settings | `ultralytics/` |
| Hugging Face settings | `huggingface/` |
| Torch, CUDA, Triton, Xet, Matplotlib, and temporary caches | `cache/` |

Local model files and exported model directories are copied into the managed model directory before loading; their originals are retained. Dependency cache paths are configured before the app imports the model libraries. Ultralytics run and dataset locations also point under this configuration directory.

## Windows release build

Requires PowerShell 7, uv, and Inno Setup 6 installed at `%LOCALAPPDATA%\Programs\Inno Setup 6`.

```powershell
pwsh -NoProfile -File scripts/build.ps1
.venv-build/Scripts/python.exe scripts/check-launch.py dist/YOLO-media-sorter-0.5.2-windows-amd64/YOLO-media-sorter-0.5.2-windows-amd64.exe build/launch.png
pwsh -NoProfile -File scripts/build-setup.ps1
```

The build uses the locked dependencies in a separate `.venv-build` environment. Versioned artifacts are written to `dist/`: a standalone application folder, a portable ZIP, and a per-user Setup executable. Python is bundled; model weights download on first use into the app configuration directory. The Windows bundle uses the locked CPU build of PyTorch.

After verifying the packaged app opens, publish `v0.5.2` as a GitHub **prerelease** and attach both the portable ZIP and Setup executable. Application version and artifact names come from `pyproject.toml`.

## Development checks

```powershell
uv run pytest
uv run ruff check app tests
```

Tests cover native YOLO result types, detector crops, video frame selection, recursive discovery, index invalidation, unclassified files, cancellation, label folder encoding, and exclusive moves.
