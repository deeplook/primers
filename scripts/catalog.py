from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalog.toml"
README_PATH = ROOT / "README.md"

REQUIRED_FIELDS = ("name", "title", "language", "path", "status")
PUBLICATION_FIELDS = ("repository", "ci_workflow", "release")
STATUSES = {"local", "published"}
GITHUB_REPOSITORY = re.compile(r"^https://github\.com/[^/]+/[^/]+$")
WORKFLOW_FILE = re.compile(r"^[^/]+\.ya?ml$")
RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")


class CatalogError(ValueError):
    """Invalid primer catalog metadata."""


def load_catalog(path: Path) -> list[dict[str, object]]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    primers = payload.get("primer")
    if not isinstance(primers, list):
        raise CatalogError("catalog.toml must contain [[primer]] records")
    return primers


def _string_field(primer: dict[str, object], key: str) -> str | None:
    if key not in primer:
        return None
    value = primer[key]
    if not isinstance(value, str):
        name = primer.get("name", "<unknown>")
        raise CatalogError(f"primer {name} field {key} must be a string")
    stripped = value.strip()
    return stripped or None


def validate_primers(primers: list[dict[str, object]]) -> str:
    names: set[str] = set()
    published = 0
    local = 0
    for primer in primers:
        values: dict[str, str] = {}
        for key in REQUIRED_FIELDS:
            value = _string_field(primer, key)
            if value is None:
                name = primer.get("name", "<unknown>")
                raise CatalogError(f"primer {name} missing {key}")
            values[key] = value
        name = values["name"]
        if name in names:
            raise CatalogError(f"duplicate name: {name}")
        names.add(name)
        status = values["status"]
        if status not in STATUSES:
            raise CatalogError(f"primer {name} has invalid status: {status}")
        present_publication = [
            key for key in PUBLICATION_FIELDS if _string_field(primer, key) is not None
        ]
        if status == "local":
            if present_publication:
                raise CatalogError(f"local primer {name} has publication fields")
            local += 1
            continue
        missing = [key for key in PUBLICATION_FIELDS if key not in present_publication]
        if missing:
            raise CatalogError(f"published primer {name} missing {missing[0]}")
        repository = _string_field(primer, "repository") or ""
        if not GITHUB_REPOSITORY.fullmatch(repository):
            raise CatalogError(f"published primer {name} has invalid repository")
        workflow = _string_field(primer, "ci_workflow") or ""
        if not WORKFLOW_FILE.fullmatch(workflow):
            raise CatalogError(f"published primer {name} has invalid ci_workflow")
        release = _string_field(primer, "release") or ""
        if not RELEASE_TAG.fullmatch(release):
            raise CatalogError(f"published primer {name} has invalid release")
        published += 1
    return f"Validated {len(primers)} primers: {published} published, {local} local."


def render_row(primer: dict[str, object]) -> str:
    title = str(primer["title"])
    language = str(primer["language"])
    path = str(primer["path"])
    if primer["status"] == "published":
        repository = str(primer["repository"])
        workflow = str(primer["ci_workflow"])
        release = str(primer["release"])
        repository_cell = f"[GitHub]({repository})"
        badge = f"{repository}/actions/workflows/{workflow}/badge.svg"
        workflow_url = f"{repository}/actions/workflows/{workflow}"
        ci_cell = f"[![CI]({badge})]({workflow_url})"
        release_cell = f"[{release}]({repository}/releases/tag/{release})"
    else:
        repository_cell = "Pending"
        ci_cell = "—"
        release_cell = "—"
    return f"| {title} | {language} | `{path}` | {repository_cell} | {ci_cell} | {release_cell} |"


def render_rows(primers: list[dict[str, object]]) -> str:
    return "\n".join(render_row(primer) for primer in primers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render primer catalog.toml")
    parser.add_argument("command", choices=["validate", "render"])
    args = parser.parse_args(argv)
    try:
        primers = load_catalog(CATALOG_PATH)
        receipt = validate_primers(primers)
    except CatalogError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.command == "validate":
        print(receipt)
        return 0
    print(render_rows(primers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
