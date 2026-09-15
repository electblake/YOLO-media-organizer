# Changelog

Notable changes are recorded here using the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
Version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/electblake/YOLO-media-sorter/compare/v0.5.2...HEAD
[0.5.2]: https://github.com/electblake/YOLO-media-sorter/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/electblake/YOLO-media-sorter/compare/v0.0.5...v0.5.1
[0.0.5]: https://github.com/electblake/YOLO-media-sorter/releases/tag/v0.0.5
