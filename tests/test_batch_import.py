"""Tests for batch-import.py idempotent import logic."""
import asyncio
import importlib.util
import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

SCRIPT = Path(__file__).parent.parent / "references/scripts/batch-import.py"


def _load():
    spec = importlib.util.spec_from_file_location("batch_import", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── get_existing_urls ─────────────────────────────────────────────────────────

def test_get_existing_urls_returns_set_of_urls():
    mod = _load()
    sources = [
        {"url": "https://ofac.treasury.gov/sanctions-list"},
        {"url": "https://eur-lex.europa.eu/regulation"},
    ]
    fake = MagicMock(returncode=0, stdout=json.dumps(sources))
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == {
        "https://ofac.treasury.gov/sanctions-list",
        "https://eur-lex.europa.eu/regulation",
    }


def test_get_existing_urls_ignores_entries_without_url():
    mod = _load()
    sources = [{"url": "https://ofac.treasury.gov"}, {"title": "Uploaded PDF", "url": ""}]
    fake = MagicMock(returncode=0, stdout=json.dumps(sources))
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == {"https://ofac.treasury.gov"}


def test_get_existing_urls_returns_empty_set_on_cli_error():
    mod = _load()
    fake = MagicMock(returncode=1, stdout="", stderr="not found")
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == set()


def test_get_existing_urls_returns_empty_set_on_bad_json():
    mod = _load()
    fake = MagicMock(returncode=0, stdout="not-json")
    with patch("subprocess.run", return_value=fake):
        result = mod.get_existing_urls("nb-123")
    assert result == set()


def test_get_existing_urls_returns_empty_set_on_exception():
    mod = _load()
    with patch("subprocess.run", side_effect=Exception("timeout")):
        result = mod.get_existing_urls("nb-123")
    assert result == set()


# ── main — skip existing ──────────────────────────────────────────────────────

def test_main_skips_already_imported_urls(tmp_path):
    """URLs already in the notebook are not re-imported."""
    mod = _load()

    already_in_nb = {"https://ofac.treasury.gov/already-there"}
    new_url = "https://eur-lex.europa.eu/new-source"

    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.sources.add_url = AsyncMock()

    with patch.object(mod, "get_existing_urls", return_value=already_in_nb), \
         patch.object(mod, "is_crawlable", return_value=(True, "html (5000 bytes)")), \
         patch("notebooklm.NotebookLMClient.from_storage", return_value=client_mock):
        result = asyncio.run(mod.main(
            "nb-test",
            ["https://ofac.treasury.gov/already-there", new_url]
        ))

    assert "https://ofac.treasury.gov/already-there" not in result["imported"]
    already_skipped = [s["url"] for s in result.get("skipped", [])]
    assert "https://ofac.treasury.gov/already-there" in already_skipped
