import logging
from typing import Any, Dict

from shared.errors.error_codes import get_error_description


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger("host.%s" % name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[HOST] %(asctime)s %(name)s %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger


def log_command_sent(
    logger: logging.Logger, command_type: str, details: Dict[str, Any]
) -> None:
    parts = ["%s=%s" % (k, v) for k, v in details.items()]
    logger.info("CMD_SENT %s | %s", command_type, " ".join(parts))


def log_state_received(logger: logging.Logger, state: Dict[str, Any]) -> None:
    logger.debug(
        "STATE alt=%.2f az=%.2f status=%s",
        state.get("current_alt_deg", 0.0),
        state.get("current_az_deg", 0.0),
        state.get("status", "unknown"),
    )


def log_error_code(logger: logging.Logger, code: int) -> None:
    desc = get_error_description(code)
    logger.error("ERROR %d: %s", code, desc)
