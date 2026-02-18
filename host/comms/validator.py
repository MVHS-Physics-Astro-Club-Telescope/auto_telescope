from typing import List

from shared.protocols.message_validator import ValidationError, validate_message
from host.utils.logger import get_logger

logger = get_logger("validator")


def validate_outgoing_command(data: dict) -> List[str]:
    try:
        errors = validate_message(data)
        if errors:
            logger.warning("Outgoing validation errors: %s", errors)
        return errors
    except ValidationError as e:
        logger.error("Outgoing validation failed: %s", e)
        return [str(e)]


def validate_incoming_response(data: dict) -> List[str]:
    msg_type = data.get("message_type")
    errors = []
    if msg_type not in ("ack", "error", "state_report"):
        errors.append("Unknown message_type: %s" % msg_type)
    if msg_type == "ack" and "command_id" not in data:
        errors.append("Ack missing command_id")
    if msg_type == "error" and "error" not in data:
        errors.append("Error response missing error field")
    if errors:
        logger.warning("Incoming validation errors: %s", errors)
    return errors


def is_valid_command(data: dict) -> bool:
    return len(validate_outgoing_command(data)) == 0
