import threading
import time

import pytest

from tests.integration.conftest import IntegrationHarness, wait_for_condition


class TestLifecycle:
    def test_clean_connect_disconnect(self):
        """Harness starts and stops without errors."""
        h = IntegrationHarness()
        h.start()

        assert h.tcp_client.is_connected()
        assert h.receiver.is_alive()

        h.stop()

        assert not h.receiver.is_alive()

    def test_pi_disconnect_detected(self, harness):
        """Pi disconnects -> Host receiver detects it."""
        assert harness.receiver.is_alive()

        harness.tcp_client.disconnect()

        assert wait_for_condition(
            lambda: not harness.receiver.is_alive(),
            timeout=3.0,
        )

    def test_commands_work_immediately(self, harness):
        """Status request succeeds right after setup."""
        ok = harness.sender.send_status_request()
        assert ok

        assert wait_for_condition(lambda: harness.host_state.has_state())

    def test_no_thread_leaks(self):
        """Thread count returns to baseline after harness stop."""
        # Let any leftover threads from other tests settle
        time.sleep(0.2)
        baseline = threading.active_count()

        h = IntegrationHarness()
        h.start()

        assert threading.active_count() > baseline

        h.stop()
        time.sleep(0.5)

        final = threading.active_count()
        assert final <= baseline + 1
