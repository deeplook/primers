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
    return f"| {title} | {repository_cell} | {ci_cell} | {release_cell} |"


def render_rows(primers: list[dict[str, object]]) -> str:
    return "\n".join(render_row(primer) for primer in primers)


BEGIN_MARKER = "<!-- BEGIN GENERATED CATALOG -->"
END_MARKER = "<!-- END GENERATED CATALOG -->"
TABLE_HEADER = (
    "| Primer | Repository | CI | Latest release |\n"
    "|---|---|---|---|"
)


def render_table(primers: list[dict[str, object]]) -> str:
    return f"{TABLE_HEADER}\n{render_rows(primers)}"


def generated_section(primers: list[dict[str, object]]) -> str:
    return f"{BEGIN_MARKER}\n{render_table(primers)}\n{END_MARKER}"


def replace_generated_section(source: str, table: str) -> str:
    begin = source.find(BEGIN_MARKER)
    end = source.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        raise CatalogError("README is missing generated catalog markers")
    end += len(END_MARKER)
    replacement = f"{BEGIN_MARKER}\n{table}\n{END_MARKER}"
    return source[:begin] + replacement + source[end:]


def check_generated_section(source: str, table: str) -> None:
    begin = source.find(BEGIN_MARKER)
    end = source.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        raise CatalogError("README is missing generated catalog markers")
    current = source[begin : end + len(END_MARKER)]
    expected = f"{BEGIN_MARKER}\n{table}\n{END_MARKER}"
    if current != expected:
        raise CatalogError(
            "README catalog table is stale; run `make catalog-update`"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render primer catalog.toml")
    parser.add_argument(
        "command",
        choices=["validate", "render", "check-readme", "update-readme"],
    )
    args = parser.parse_args(argv)
    try:
        primers = load_catalog(CATALOG_PATH)
        receipt = validate_primers(primers)
        if args.command == "validate":
            print(receipt)
            return 0
        if args.command == "render":
            print(render_rows(primers))
            return 0
        table = render_table(primers)
        if args.command == "check-readme":
            check_generated_section(README_PATH.read_text(encoding="utf-8"), table)
            print("README catalog table matches catalog.toml.")
            return 0
        updated = replace_generated_section(README_PATH.read_text(encoding="utf-8"), table)
        README_PATH.write_text(updated, encoding="utf-8")
        print("Updated README catalog table from catalog.toml.")
        return 0
    except CatalogError as exc:
        print(str(exc), file=sys.stderr)
        return 1



if __name__ == "__main__":
    raise SystemExit(main())
