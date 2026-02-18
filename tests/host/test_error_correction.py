import time

import pytest

from host.control.error_correction import PIDController


class TestPIDController:
    def test_proportional_only(self):
        pid = PIDController(kp=2.0, ki=0.0, kd=0.0, output_min=-10.0, output_max=10.0)
        output = pid.compute(5.0)
        assert output == pytest.approx(10.0)

    def test_proportional_small(self):
        pid = PIDController(kp=0.5, ki=0.0, kd=0.0, output_min=-10.0, output_max=10.0)
        output = pid.compute(3.0)
        assert output == pytest.approx(1.5)

    def test_integral_accumulates(self):
        pid = PIDController(kp=0.0, ki=1.0, kd=0.0, output_min=-100.0, output_max=100.0)
        pid.compute(1.0)
        time.sleep(0.05)
        output = pid.compute(1.0)
        assert output > 0

    def test_derivative_responds_to_change(self):
        pid = PIDController(kp=0.0, ki=0.0, kd=1.0, output_min=-100.0, output_max=100.0)
        pid.compute(0.0)
        time.sleep(0.05)
        output = pid.compute(10.0)
        assert output > 0

    def test_clamping_max(self):
        pid = PIDController(kp=100.0, ki=0.0, kd=0.0, output_min=0.0, output_max=1.0)
        output = pid.compute(5.0)
        assert output == pytest.approx(1.0)

    def test_clamping_min(self):
        pid = PIDController(kp=100.0, ki=0.0, kd=0.0, output_min=0.0, output_max=1.0)
        output = pid.compute(-5.0)
        assert output == pytest.approx(0.0)

    def test_reset_clears_state(self):
        pid = PIDController(kp=0.0, ki=1.0, kd=0.0, output_min=-100.0, output_max=100.0)
        pid.compute(10.0)
        time.sleep(0.05)
        pid.compute(10.0)
        pid.reset()
        output = pid.compute(0.0)
        assert output == pytest.approx(0.0)

    def test_zero_error_gives_zero(self):
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0, output_min=-10.0, output_max=10.0)
        output = pid.compute(0.0)
        assert output == pytest.approx(0.0)
