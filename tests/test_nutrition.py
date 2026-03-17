"""Tests for the nutrition calculator."""

import pytest

from nutrisnap.analyzer.food_detector import DetectionResult
from nutrisnap.analyzer.nutrition import NutritionCalculator
from nutrisnap.database.usda import USDADatabase


@pytest.fixture
def calculator():
    return NutritionCalculator()


class TestNutritionCalculator:
    def test_calculate_known_food(self, calculator):
        detection = DetectionResult(food_name="banana", confidence=0.9)
        food = calculator.calculate(detection)
        assert food is not None
        assert food.name == "banana"
        assert food.portion_grams > 0
        assert food.nutrition_actual.calories > 0
        # Banana is 89 cal/100g, standard portion is 118g
        expected_cal = 89 * 118 / 100
        assert food.nutrition_actual.calories == pytest.approx(expected_cal, abs=1)

    def test_calculate_unknown_food(self, calculator):
        detection = DetectionResult(food_name="nonexistent", confidence=0.5)
        assert calculator.calculate(detection) is None

    def test_calculate_multiple(self, calculator):
        detections = [
            DetectionResult(food_name="apple", confidence=0.9),
            DetectionResult(food_name="banana", confidence=0.8),
            DetectionResult(food_name="nonexistent", confidence=0.5),
        ]
        foods = calculator.calculate_multiple(detections)
        assert len(foods) == 2  # nonexistent skipped
        names = {f.name for f in foods}
        assert names == {"apple", "banana"}

    def test_total_nutrition(self, calculator):
        detections = [
            DetectionResult(food_name="apple", confidence=0.9),
            DetectionResult(food_name="banana", confidence=0.8),
        ]
        foods = calculator.calculate_multiple(detections)
        total = calculator.total_nutrition(foods)
        assert total.calories > 0
        assert total.protein >= 0

    def test_lookup_food_custom_portion(self, calculator):
        food = calculator.lookup_food("chicken_breast", portion_grams=200)
        assert food is not None
        assert food.portion_grams == 200
        # 165 cal/100g * 2 = 330
        assert food.nutrition_actual.calories == pytest.approx(330, abs=1)

    def test_lookup_food_not_found(self, calculator):
        assert calculator.lookup_food("imaginary_food") is None
