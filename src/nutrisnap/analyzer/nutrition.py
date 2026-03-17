"""Nutrition calculation from detected food items."""

from __future__ import annotations

from nutrisnap.analyzer.food_detector import DetectionResult
from nutrisnap.analyzer.portion import PortionEstimator
from nutrisnap.database.usda import USDADatabase
from nutrisnap.models import Food, NutritionInfo


class NutritionCalculator:
    """Calculates nutritional values for detected foods.

    Combines the USDA nutrition database with portion estimates to produce
    accurate per-serving nutritional breakdowns for detected food items.
    """

    def __init__(
        self,
        db: USDADatabase | None = None,
        portion_estimator: PortionEstimator | None = None,
    ) -> None:
        self.db = db or USDADatabase()
        self.portion_estimator = portion_estimator or PortionEstimator()

    def calculate(self, detection: DetectionResult) -> Food | None:
        """Calculate nutrition for a single detected food item.

        Args:
            detection: DetectionResult from the food detector.

        Returns:
            A Food model with full nutrition info, or None if the food
            is not in the database.
        """
        nutrition = self.db.lookup(detection.food_name)
        if nutrition is None:
            return None

        portion_grams = self.portion_estimator.estimate(detection.food_name)
        scale_factor = portion_grams / 100.0
        actual_nutrition = nutrition.scale(scale_factor)

        return Food(
            name=detection.food_name,
            confidence=detection.confidence,
            portion_grams=portion_grams,
            nutrition_per_100g=nutrition,
            nutrition_actual=actual_nutrition,
            category=self.db.get_category(detection.food_name),
        )

    def calculate_multiple(self, detections: list[DetectionResult]) -> list[Food]:
        """Calculate nutrition for multiple detected foods.

        Args:
            detections: List of DetectionResult objects.

        Returns:
            List of Food objects (items not in DB are skipped).
        """
        foods: list[Food] = []
        for detection in detections:
            food = self.calculate(detection)
            if food is not None:
                foods.append(food)
        return foods

    def total_nutrition(self, foods: list[Food]) -> NutritionInfo:
        """Sum up nutrition across a list of foods.

        Args:
            foods: List of Food objects.

        Returns:
            Combined NutritionInfo for all foods.
        """
        total = NutritionInfo.zero()
        for food in foods:
            total = total + food.nutrition_actual
        return total

    def lookup_food(self, food_name: str, portion_grams: float = 100.0) -> Food | None:
        """Manually look up nutrition for a food by name and portion.

        Args:
            food_name: Name of the food.
            portion_grams: Serving size in grams.

        Returns:
            Food object or None if not found.
        """
        nutrition = self.db.lookup(food_name)
        if nutrition is None:
            return None

        scale_factor = portion_grams / 100.0
        return Food(
            name=food_name,
            confidence=1.0,
            portion_grams=portion_grams,
            nutrition_per_100g=nutrition,
            nutrition_actual=nutrition.scale(scale_factor),
            category=self.db.get_category(food_name),
        )
