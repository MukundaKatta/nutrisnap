"""Tests for the portion estimator."""

import pytest

from nutrisnap.analyzer.portion import PortionEstimator


@pytest.fixture
def estimator():
    return PortionEstimator()


class TestPortionEstimator:
    def test_known_food(self, estimator):
        portion = estimator.estimate("apple")
        assert portion == 182

    def test_unknown_food_default(self, estimator):
        portion = estimator.estimate("unknown_alien_food")
        assert portion == 100.0

    def test_scale_factor(self, estimator):
        base = estimator.estimate("banana", image_scale_factor=1.0)
        doubled = estimator.estimate("banana", image_scale_factor=2.0)
        assert doubled == pytest.approx(base * 2.0, abs=0.1)

    def test_standard_portion(self, estimator):
        assert estimator.get_standard_portion("egg_whole") == 50

    def test_supported_foods_not_empty(self, estimator):
        assert len(estimator.supported_foods) > 100

    def test_spaces_in_name(self, estimator):
        assert estimator.estimate("chicken breast") == 172

    def test_all_usda_foods_have_portions(self, estimator):
        """Every food in portions list should return a positive value."""
        for food in estimator.supported_foods:
            assert estimator.estimate(food) > 0
