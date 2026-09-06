from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import catalog  # noqa: E402


def local(name: str, title: str, *, language: str = "Python") -> dict[str, str]:
    return {
        "name": name,
        "title": title,
        "language": language,
        "path": f"../{name}-primer",
        "status": "local",
    }


def published(name: str, title: str) -> dict[str, str]:
    return {
        "name": name,
        "title": title,
        "language": "Python",
        "path": f"../{name}-primer",
        "status": "published",
        "repository": f"https://github.com/deeplook/{name}-primer",
        "ci_workflow": "check.yml",
        "release": "v0.1.0",
    }


class ValidateCatalogTests(unittest.TestCase):
    def test_current_catalog_is_valid(self) -> None:
        primers = catalog.load_catalog(ROOT / "catalog.toml")
        receipt = catalog.validate_primers(primers)
        self.assertEqual(receipt, "Validated 25 primers: 5 published, 20 local.")

    def test_duplicate_name_is_rejected(self) -> None:
        primers = [local("nats", "NATS"), local("nats", "NATS Clone")]
        with self.assertRaisesRegex(catalog.CatalogError, "duplicate name: nats"):
            catalog.validate_primers(primers)

    def test_local_record_with_publication_fields_is_rejected(self) -> None:
        primer = local("rag", "RAG")
        primer["repository"] = "https://github.com/deeplook/rag-primer"
        with self.assertRaisesRegex(catalog.CatalogError, "local primer rag has publication fields"):
            catalog.validate_primers([primer])

    def test_published_record_missing_required_field_is_rejected(self) -> None:
        primer = published("openai", "OpenAI API")
        del primer["release"]
        with self.assertRaisesRegex(catalog.CatalogError, "published primer openai missing release"):
            catalog.validate_primers([primer])


class RenderCatalogTests(unittest.TestCase):
    def test_render_includes_published_urls_and_keeps_rag_pending(self) -> None:
        primers = catalog.load_catalog(ROOT / "catalog.toml")
        catalog.validate_primers(primers)
        rows = catalog.render_rows(primers)
        self.assertEqual(len(rows.splitlines()), len(primers))
        for name in ("agents", "nats", "openai", "pyspark", "ray"):
            self.assertIn(f"https://github.com/deeplook/{name}-primer", rows)
        self.assertIn("| RAG | Python | `../rag-primer` | Pending | — | — |", rows)
        self.assertNotIn("deeplook/rag-primer", rows)


class ReadmeCatalogTests(unittest.TestCase):
    def test_generated_table_includes_header_and_one_row_per_primer(self) -> None:
        primers = catalog.load_catalog(ROOT / "catalog.toml")
        table = catalog.render_table(primers)
        lines = table.splitlines()
        self.assertEqual(
            lines[0],
            "| Primer | Language | Local path | Repository | CI | Latest release |",
        )
        self.assertEqual(lines[1], "|---|---|---|---|---|---|")
        self.assertEqual(len(lines) - 2, len(primers))

    def test_update_readme_replaces_only_the_marked_section(self) -> None:
        primers = [local("sqlite", "SQLite")]
        source = (
            "Intro\n"
            "\n"
            "<!-- BEGIN GENERATED CATALOG -->\n"
            "old table\n"
            "<!-- END GENERATED CATALOG -->\n"
            "\n"
            "Policy\n"
        )
        updated = catalog.replace_generated_section(source, catalog.render_table(primers))
        self.assertTrue(updated.startswith("Intro\n"))
        self.assertTrue(updated.endswith("Policy\n"))
        self.assertIn("| SQLite | Python | `../sqlite-primer` | Pending | — | — |", updated)
        self.assertNotIn("old table", updated)

    def test_check_readme_rejects_stale_generated_section(self) -> None:
        primers = [local("sqlite", "SQLite")]
        stale = (
            "<!-- BEGIN GENERATED CATALOG -->\n"
            "stale\n"
            "<!-- END GENERATED CATALOG -->\n"
        )
        with self.assertRaisesRegex(catalog.CatalogError, "README catalog table is stale"):
            catalog.check_generated_section(stale, catalog.render_table(primers))


if __name__ == "__main__":
    unittest.main()
