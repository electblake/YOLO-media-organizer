# Changelog

## [Unreleased]

### Added

- Live file totals, matched counts and percentages, and remaining files to move beside Open media folder.
- Print individual scan failures and display the latest error and failure count while continuing with remaining files.

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

[Unreleased]: https://github.com/electblake/YOLO-media-organizer/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/electblake/YOLO-media-organizer/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/electblake/YOLO-media-organizer/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/electblake/YOLO-media-organizer/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/electblake/YOLO-media-organizer/compare/v0.5.2...v0.6.0
[0.5.2]: https://github.com/electblake/YOLO-media-organizer/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/electblake/YOLO-media-organizer/compare/v0.0.5...v0.5.1
[0.0.5]: https://github.com/electblake/YOLO-media-organizer/releases/tag/v0.0.5
