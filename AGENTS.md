never fucking edit the readme unless explicitly demanded. yours a terrible fucking writer.

## Release checklist

1. Review changes since the latest GitHub release.
2. Bump the project SemVer appropriately (patch: fixes, minor: features, major: breaking changes). Keep uv.lock untracked and out of installers.
3. Move Unreleased changes into a dated changelog entry for the new version.
4. Run tests and checks; build the Windows installer and verify packaged app launch.
5. Commit release changes, tag the version, and push to GitHub.
6. Publish the GitHub release with concise notes, the installer, and any verification limitations. Do not generate or publish hashes or checksum files.
7. Verify the published installer asset; report the release link.
