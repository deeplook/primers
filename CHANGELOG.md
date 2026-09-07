# Changelog

## [Unreleased]

### Added
- Prepared the catalog for public GitHub publication with an MIT license,
  Python 3.12 pinning, and a Makefile quality gate.
- Made every primer record carry an explicit title and local or published
  status.
- Added a dependency-free catalog validator and Markdown renderer.
- Generated the README catalog table from `catalog.toml`.
- Added GitHub Actions CI that validates catalog metadata and README
  generation.

### Changed
- Removed the maintainer policy section from the README so the catalog
  page stays reader-facing.
- Dropped the EP-133 K.O.II primer from the catalog.
- Simplified the catalog table to repository, CI, and release columns.
