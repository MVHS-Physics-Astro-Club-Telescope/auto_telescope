from typing import List

from shared.protocols.message_validator import ValidationError, validate_message
from pi.utils.logger import get_logger

logger = get_logger("validator")


def validate_incoming_command(data: dict) -> List[str]:
    try:
        errors = validate_message(data)
        if errors:
            logger.warning("Validation errors: %s", errors)
        return errors
    except ValidationError as e:
        logger.error("Validation failed: %s", e)
        return [str(e)]


def is_valid_command(data: dict) -> bool:
    return len(validate_incoming_command(data)) == 0
