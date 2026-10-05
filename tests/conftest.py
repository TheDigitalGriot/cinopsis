"""Suite-wide guards for the stage contract ``transcript-browser-default`` (H0/H1).

HARD CONSTRAINT: no test may ever launch a browser, instantiate a webdriver, or
load a YouTube page. These autouse fixtures make that STRUCTURAL rather than a
matter of every test author remembering:

  * ``chrome_session._probe`` is replaced with a stub returning None, so even an
    un-mocked ``acquire_session()`` can never find (and attach to) a real Chrome
    that happens to be listening on the debug port - it raises F1 instead.
  * ``selenium.webdriver.Chrome`` is replaced with a raiser, so a stray
    ``build_driver()`` can never create a driver, attached or otherwise.

A test that wants a different probe result overrides ``_probe`` itself; none
may ever give it a real one.
"""
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture(autouse=True)
def _never_touch_a_browser(monkeypatch):
    import chrome_session

    monkeypatch.setattr(chrome_session, "_probe", lambda *a, **k: None)

    try:
        from selenium import webdriver
    except Exception:       # selenium not installed: nothing to guard
        return

    def _boom(*a, **k):
        raise AssertionError(
            "H1: a test tried to instantiate a Selenium webdriver - tests must be "
            "offline and browser-free")

    monkeypatch.setattr(webdriver, "Chrome", _boom)
