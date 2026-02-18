import logging
from typing import Any, Dict

from shared.errors.error_codes import get_error_description


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"pi.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[PI] %(asctime)s %(name)s %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


def log_hardware_event(
    logger: logging.Logger, event: str, details: Dict[str, Any]
) -> None:
    parts = [f"{k}={v}" for k, v in details.items()]
    logger.info("HW_EVENT %s | %s", event, " ".join(parts))


def log_error_code(logger: logging.Logger, code: int) -> None:
    desc = get_error_description(code)
    logger.error("ERROR %d: %s", code, desc)
