# Changelog

## [Unreleased]

## [0.9.0] - 2026-09-19

### Added

- Configure and persist the number of scan results added to the preview between interface updates.

## [0.8.3] - 2026-09-19

### Changed

- Prepare large scan previews in incremental chunks with visible progress and completion logging, keeping the interface responsive between batches.
- Improve README presentation and documentation links.

## [0.8.2] - 2026-09-16

### Changed

- Replace the project license with MIT and keep Ultralytics documentation links in the README.
- Document YOLO versions for model presets.

### Removed

- Remove the unused video position option and legacy snapshot extraction; folder scans use Ultralytics video stride.

### Fixed

- Show actionable missing-credential errors before downloading Ultralytics Platform or Hugging Face models.

## [0.8.1] - 2026-09-16

### Added

- Configure inference batch size, precision, compilation, image size, and video stride; save and reset these options with the app configuration.
- Show scan speed and estimated remaining time.
- Copy, download, and open scan logs or their containing folder from the console controls.
- Include scan options, runtime versions, model details, inference arguments, and completion details in scan logs.
- Show the app version in the window title and heading, with a project website button.
- Add the RoyRud1902/yolo11n-text model preset.
- Configure result streaming and live-stream buffering, with hover hints for inference and output settings.
- Save annotated results, object crops, and text labels in a persistent run directory for each media folder; open it with Open run results.
- Optionally move videos that fail to open into a configurable quarantine subfolder and re-run the scan.

### Changed

- Rename the Sort Media tab to Organize and keep scan controls above the resizable label area.
- Move model selection and scan confidence controls to the Models tab.
- Report the number of files moved, or indicate when no files were moved.
- Resolve installer dependencies during setup without requiring or bundling `uv.lock`.

### Fixed

- Display scan failures and their tracebacks in the console and log while preserving the original failure.
- Disable file organization while busy or when no files remain in the move plan.

### Removed

- Remove recursive-scan controls and the `--recursive` / `--no-recursive` arguments; scans use the selected folder's immediate media files.
- Stop tracking `uv.lock` in the repository.
- Remove image hover previews and preview thumbnail generation from results and label filters.
- Remove pytest temporary artifacts from Git history and ignore pytest temporary folders.

## [0.7.3] - 2026-09-15

### Added

- Save native Ultralytics verbose output to a per-scan log and show it in an auto-scrolling app console.
- Report the inference device selected by Ultralytics, including the CUDA device name, in the UI and scan log.
- Require Ultralytics automatic device selection to detect CUDA in the test suite.

### Changed

- Pass the selected media folder to one native streaming Ultralytics prediction run and publish results when the run finishes.
- Show total files, labels, files to move, move percentage, and file-level `Scanning (X/Y)` progress without counting video frames as files.
- Install CUDA 13.0 PyTorch and torchvision by default on Windows and simplify the installer to one NVIDIA CUDA dependency path.

### Removed

- Remove the misleading matched count and the CPU/GPU dependency-group and installer selection paths.

## [0.7.2] - 2026-09-15

### Added

- Live file totals, matched counts and percentages, and remaining files to move beside Open media folder.
- Print individual scan failures and display the latest error and failure count while continuing with remaining files.

### Changed

- Use the white Ymo icon for the app window, shortcuts, and File Explorer integration, and the dark Ymo icon for the installer.
- Rename Preview sorting to Start Media Scan and Sort media to Organize Files.

## [0.7.1] - 2026-09-15

### Changed

- Show model resolution, download, extraction, weight loading, and class reading in the bottom status message.
- Show download bytes and percentages for Hugging Face and direct URL models, with an animated progress bar during loading stages.
- Confirm when saved API key overrides have been applied.
- Route Hugging Face class-loading progress to the GUI without requiring a console.

## [0.7.0] - 2026-09-15

### Changed

- One Windows installer with CPU or NVIDIA CUDA 13.0 selection during setup.
- Setup downloads Python 3.12.10 and locked dependencies into a private environment.
- Re-running setup can switch between CPU and GPU dependencies.
- Build the installer with `./scripts/build-setup.ps1`.

### Removed

- PyInstaller bundles, separate CPU/GPU installers, split archives, and wheel build scripts.
- Separate build instructions; install and build steps are in the README.

## [0.6.2] - 2026-09-15

### Added

- CPU and CUDA 13.0 dependency groups with matching PyTorch and torchvision builds.
- Separate CPU and CUDA 13.0 Windows installers.
- Python wheel build script and installation instructions.

### Changed

- Build both Windows variants by default in isolated environments, with `-Backend cpu` or `-Backend gpu` to select one.
- Publish only installers, splitting files larger than 500 MB into 7z volumes.
- Moved build instructions from README.md to BUILD.md.

## [0.6.1] - 2026-09-15

### Changed

- Renamed the application, command, settings directory, and Windows packages to YOLO Media Organizer.
- Shortened the README and moved model details to Models.md.
- Added YOLOmo artwork and a direct Windows installer link.

## [0.6.0] - 2026-09-15

### Added

- Model class browser with background loading, case-insensitive filtering, and sortable class IDs and labels.
- Extras tab with per-user File Explorer context menu installation for folders, folder backgrounds, and drives.
- Explorer launch support that opens Sort Media with the selected folder as the media source.

### Changed

- Split configuration and results into resizable side-by-side panes, with scrollable scan settings and a resizable organize label area.
- Keep results, actions, and progress visible across Scan, Settings, and Extras tabs.
- Include divider positions in explicit configuration saving, reset, and user defaults; use a 1440x960 default window.

## [0.5.2] - 2026-09-15

### Removed

- The `likewendy/yolo26n-cls-porn` model preset from the model dropdown and model documentation.

## [0.5.1] - 2026-09-15

### Added

- Scan and Settings tabs below the app title.
- Pydantic user configuration and saved app state in the platformdirs user config directory.
- Explicit launch arguments with precedence over saved state, user configuration, and built-in defaults.
- Save config, Reset config, and Set default config controls for manually saving state and managing user defaults.
- Settings view showing the config path and environment API keys, with optional Ultralytics and Hugging Face overrides saved only through Save settings.
- Case-insensitive partial-text filtering for the labels checklist that preserves checked labels and the move plan.

### Changed

- Labels use a full-width, scrollable vertical checklist.
- The organize section is titled `organize`.
- UI changes remain unsaved until the user explicitly saves; launching, resizing, switching tabs, and closing do not write config or state.

## [0.0.5] - 2026-09-15

### Added

- Initial Windows prerelease with a portable ZIP, per-user installer, and SHA-256 checksums.
- Image and video-snapshot scanning with compatible Ultralytics classification and detection models.
- Indexed predictions, confidence and count filters, label selection, sortable preview, and moves into label-named folders.
- Model presets from Hugging Face, GitHub, and Ultralytics Platform.
- Repeatable PyInstaller and Inno Setup build scripts with an executable launch check.

[Unreleased]: https://github.com/electblake/YOLO-media-organizer/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/electblake/YOLO-media-organizer/compare/v0.8.3...v0.9.0
[0.8.3]: https://github.com/electblake/YOLO-media-organizer/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/electblake/YOLO-media-organizer/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/electblake/YOLO-media-organizer/compare/v0.7.3...v0.8.1
[0.7.3]: https://github.com/electblake/YOLO-media-organizer/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/electblake/YOLO-media-organizer/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/electblake/YOLO-media-organizer/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/electblake/YOLO-media-organizer/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/electblake/YOLO-media-organizer/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/electblake/YOLO-media-organizer/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/electblake/YOLO-media-organizer/compare/v0.5.2...v0.6.0
[0.5.2]: https://github.com/electblake/YOLO-media-organizer/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/electblake/YOLO-media-organizer/compare/v0.0.5...v0.5.1
[0.0.5]: https://github.com/electblake/YOLO-media-organizer/releases/tag/v0.0.5
