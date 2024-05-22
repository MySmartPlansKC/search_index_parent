# Search Index Parent

# Changelog

## [1.2.0] - 2024-05-21
### Fixed
- Corrected file processing logic.
- Revamped logging system to properly track files.

---

## [1.1.5] - 2024-05-17
### Added
- Added file lock for system process to ensure file access
- Moved marker files to their own text file for better separation of concerns.

### Changed
- Adjusted logging to display the destination without the filename appended to the end.
- Removed excessive messages for cleaner production runs

---

## [1.1.4] - 2024-05-17
### Added
- Detailed logging to error messages for better tracking
- Log designation to track the current folder being processed

---

## [1.1.3] - 2024-05-16

### Added
- Added a processed flag to avoid counting/missing items

### Fixed
- Corrected bug that was overwriting the search_index.xml

---

## [1.1.2] - 2024-05-16
### Added
- Added configuration to resume if program gets terminated before completing.

---

## [1.1.1] - 2024-05-16
### Changed
- Reconfigured search_index.xml aggregation for better accuracy.

---

## [1.1.0] - 2024-05-15
### Added
- Configured logging for more detailed logging information
- Special path for "NO CLASSIFICATION" folder to search its subfolders
- Updated file processing for more performance.

### Fixed
- Incorrect logging notations.

---

## [1.0.0] - 2024-05-15
### Added
- Initial release of Search Index Builder.
- Processes PDF, text, and log files.
- Creates `search_index.xml` files for each directory and subdirectory.
- Generates an accumulated `search_index.xml` file in the root directory.
- Includes versioning in the log file.