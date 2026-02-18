from typing import Dict, List, Optional

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.config.ui_params import STATUS_LINE_WIDTH
from host.state.session_logs import LogEntry


def format_state(state: Optional[TelescopeState]) -> str:
    if state is None:
        return "No state received from Pi yet."

    lines = [
        "=" * STATUS_LINE_WIDTH,
        "  Position:  alt=%.4f  az=%.4f" % (
            state.current_alt_deg, state.current_az_deg,
        ),
    ]

    if state.target_alt_deg is not None and state.target_az_deg is not None:
        lines.append(
            "  Target:    alt=%.4f  az=%.4f" % (
                state.target_alt_deg, state.target_az_deg,
            )
        )

    status_str = state.status.value if hasattr(state.status, "value") else str(state.status)
    lines.append("  Status:    %s" % status_str)

    if state.focus_position is not None:
        lines.append("  Focus:     %d" % state.focus_position)

    if state.is_tracking:
        lines.append("  Tracking:  YES")

    if state.error_codes:
        lines.append("  Errors:    %s" % state.error_codes)

    lines.append("=" * STATUS_LINE_WIDTH)
    return "\n".join(lines)


def format_tracking_info(info: Dict) -> str:
    if not info.get("tracking"):
        return "Not tracking"

    return "Tracking %s | target alt=%.2f az=%.2f | error=%.4f deg | %s" % (
        info.get("target", "?"),
        info.get("target_alt", 0.0),
        info.get("target_az", 0.0),
        info.get("error_deg", 0.0),
        "OK" if info.get("within_tolerance") else "CORRECTING",
    )


def format_log_entries(entries: List[LogEntry], count: int = 10) -> str:
    recent = entries[-count:]
    if not recent:
        return "No log entries."

    lines = []
    for entry in recent:
        import time
        ts = time.strftime("%H:%M:%S", time.localtime(entry.timestamp))
        lines.append("[%s] %s: %s" % (ts, entry.category, entry.data))
    return "\n".join(lines)
