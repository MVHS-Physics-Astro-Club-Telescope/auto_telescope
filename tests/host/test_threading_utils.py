import threading
import time

import pytest

from host.utils.threading_utils import PeriodicTask, StoppableThread


class TestStoppableThread:
    def test_start_and_stop(self):
        called = threading.Event()

        def worker(stop_event):
            called.set()
            stop_event.wait()

        st = StoppableThread(target=worker, name="test-thread")
        st.start()
        assert called.wait(timeout=1.0)
        assert st.is_alive()
        st.stop()
        assert not st.is_alive()

    def test_double_start_is_safe(self):
        def worker(stop_event):
            stop_event.wait()

        st = StoppableThread(target=worker)
        st.start()
        st.start()  # should not create a second thread
        st.stop()

    def test_stop_event_is_accessible(self):
        def worker(stop_event):
            stop_event.wait()

        st = StoppableThread(target=worker)
        assert isinstance(st.stop_event, threading.Event)
        st.start()
        st.stop()


class TestPeriodicTask:
    def test_runs_multiple_times(self):
        counter = {"n": 0}
        lock = threading.Lock()

        def increment():
            with lock:
                counter["n"] += 1

        pt = PeriodicTask(target=increment, hz=100, name="test-periodic")
        pt.start()
        time.sleep(0.15)
        pt.stop()

        with lock:
            assert counter["n"] >= 5

    def test_stop_halts_execution(self):
        counter = {"n": 0}

        def increment():
            counter["n"] += 1

        pt = PeriodicTask(target=increment, hz=100)
        pt.start()
        time.sleep(0.05)
        pt.stop()
        count_after_stop = counter["n"]
        time.sleep(0.05)
        assert counter["n"] == count_after_stop

    def test_is_alive(self):
        def noop():
            pass

        pt = PeriodicTask(target=noop, hz=10)
        assert not pt.is_alive()
        pt.start()
        assert pt.is_alive()
        pt.stop()
        assert not pt.is_alive()
