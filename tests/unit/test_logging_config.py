"""Tests unitaires de la configuration du logging (app/core/logging_config.py)."""

import logging
from collections.abc import Iterator

import pytest

from app.core.logging_config import HANDLER_NAME, setup_logging


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    """Remet le logger racine dans son état initial après chaque test."""
    root_logger = logging.getLogger()
    level, handlers = root_logger.level, root_logger.handlers[:]
    yield
    root_logger.setLevel(level)
    root_logger.handlers[:] = handlers


def test_root_level_is_applied() -> None:
    setup_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG


def test_repeated_calls_do_not_duplicate_handler() -> None:
    setup_logging("INFO")
    setup_logging("INFO")
    ours = [h for h in logging.getLogger().handlers if h.get_name() == HANDLER_NAME]
    assert len(ours) == 1


def test_noisy_libraries_only_show_warnings() -> None:
    setup_logging("DEBUG")
    assert logging.getLogger("httpx").level == logging.WARNING


def test_messages_below_level_are_filtered(caplog: pytest.LogCaptureFixture) -> None:
    setup_logging("WARNING")
    logger = logging.getLogger("app.demo")
    logger.info("message info")
    logger.warning("message warning")
    assert "message warning" in caplog.text
    assert "message info" not in caplog.text
