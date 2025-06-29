# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- Auto-commit: Save local changes

## [1.19.2] - 2023-12-08

### Security
- Bumped cryptography from 41.0.5 to 41.0.6 (#137)

### Added
- Enable Python 3.12 support in CI (#136)
- Upgrade manylinux_x_y for better platform compatibility (#136)

### Changed
- Cleanup repository structure (#133)
- Bumped minimum supported Python version to 3.8 (Python 3.6 and 3.7 are EOL)
- Upgraded CircleCI to Python 3.11
- Updated GitHub Actions macOS targets
- Updated poetry lock file

### Removed
- Removed Python 3.7 from GitHub Actions (EOL)

## [1.19.1] - 2023-XX-XX

### Added
- Automated build support for Python 3.11
- GitHub workflows including PyPI releases from CI (#114)

### Fixed
- Include upstream-quickjs/VERSION in sdist (#111)
- Use JS_UpdateStackTop to fix testing errors on Windows (#109)

## [1.19.0] - 2023-XX-XX

### Added
- Context.globalThis property (#104)
- Test ensuring that the globalThis property is readonly (#105)

### Changed
- Updated release and maintainer information (#106)
- Added more precise information about submodule (#103)

### Fixed
- Typo: accross -> across (#102)

## Previous Releases

### Binary Support History
- 1.19.2 and later: Python 3.7-3.10, 64-bit for Windows, macOS and GNU/Linux
- 1.18.0-1.19.1: No binaries provided
- 1.5.1–1.17.0: Python 3.9, 64-bit for Windows
- 1.5.0 and earlier: Python 3.7, 64-bit for Windows