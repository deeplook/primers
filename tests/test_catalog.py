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
        self.assertEqual(receipt, "Validated 26 primers: 5 published, 21 local.")

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


if __name__ == "__main__":
    unittest.main()
