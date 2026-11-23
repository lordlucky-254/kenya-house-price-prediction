"""End-to-end smoke tests for the Streamlit application using AppTest."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "src" / "app.py"


def test_app_renders_without_exceptions() -> None:
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    assert not at.exception
    assert len(at.metric) == 4
    assert len(at.tabs) == 4


def test_app_handles_empty_county_selection_gracefully() -> None:
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    at.sidebar.multiselect[0].set_value([]).run()
    assert not at.exception
    assert len(at.warning) >= 1


def test_app_sql_explorer_button_executes() -> None:
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()

    run_btn = next(btn for btn in at.button if btn.label == "Run SQL Query")
    run_btn.click().run()
    assert not at.exception
    assert any("Returned" in msg.value for msg in at.success)
