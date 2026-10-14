"""The locale catalogues must stay in sync (AGENTS.md: every string in both)."""

from __future__ import annotations

from app.i18n.translator import DEFAULT_LOCALE, LOCALES_DIR, _catalog


def _locales() -> list[str]:
    return sorted(path.stem for path in LOCALES_DIR.glob("*.json"))


def _keys(locale: str) -> set[str]:
    return set(_catalog(locale))


def test_catalogs_share_the_same_keys():
    default = _keys(DEFAULT_LOCALE)
    assert default, "the default catalogue is empty"
    for locale in _locales():
        missing = default - _keys(locale)
        assert not missing, f"{locale}.json is missing {sorted(missing)}"
        extra = _keys(locale) - default
        assert not extra, f"{locale}.json has extra keys: {sorted(extra)}"


def test_no_catalog_has_blank_messages():
    for locale in _locales():
        blank = sorted(k for k, text in _catalog(locale).items() if not text.strip())
        assert not blank, f"{locale}.json has blank messages: {blank}"
