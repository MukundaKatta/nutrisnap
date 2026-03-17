"""Tests for the meal tracker."""

from datetime import date

import pytest

from nutrisnap.database.meals import MealTracker
from nutrisnap.models import Food, Meal, MealType, NutritionInfo


def _make_food(name: str, calories: float) -> Food:
    n = NutritionInfo(calories=calories, protein=10, carbs=20, fat=5, fiber=3)
    return Food(
        name=name, confidence=0.9, portion_grams=100,
        nutrition_per_100g=n, nutrition_actual=n,
    )


class TestMealTracker:
    def test_add_meal(self):
        tracker = MealTracker()
        meal = Meal(meal_type=MealType.LUNCH, foods=[_make_food("test", 500)])
        log = tracker.add_meal(meal)
        assert log.meal_count == 1
        assert log.total_calories == 500

    def test_log_food_convenience(self):
        tracker = MealTracker()
        foods = [_make_food("a", 200), _make_food("b", 300)]
        meal = tracker.log_food(foods, meal_type=MealType.DINNER)
        assert meal.total_calories == 500

    def test_daily_totals(self):
        tracker = MealTracker()
        d = date(2026, 3, 1)
        tracker.add_meal(
            Meal(meal_type=MealType.BREAKFAST, foods=[_make_food("x", 400)]),
            log_date=d,
        )
        tracker.add_meal(
            Meal(meal_type=MealType.LUNCH, foods=[_make_food("y", 600)]),
            log_date=d,
        )
        totals = tracker.get_daily_totals(log_date=d)
        assert totals.calories == 1000

    def test_remaining_calories(self):
        tracker = MealTracker()
        d = date(2026, 3, 1)
        tracker.add_meal(
            Meal(meal_type=MealType.LUNCH, foods=[_make_food("x", 800)]),
            log_date=d,
        )
        goals = NutritionInfo(
            calories=2000, protein=60, carbs=250, fat=70, fiber=30,
            vitamin_a=900, vitamin_c=90, calcium=1000, iron=8, potassium=3400,
        )
        remaining = tracker.get_remaining(goals, log_date=d)
        assert remaining["calories"] == 1200

    def test_total_meals_logged(self):
        tracker = MealTracker()
        for i in range(5):
            tracker.add_meal(
                Meal(meal_type=MealType.SNACK, foods=[_make_food(f"f{i}", 100)]),
                log_date=date(2026, 3, i + 1),
            )
        assert tracker.total_meals_logged == 5
        assert tracker.total_days_tracked == 5

    def test_get_history(self):
        tracker = MealTracker()
        today = date.today()
        tracker.add_meal(
            Meal(meal_type=MealType.LUNCH, foods=[_make_food("x", 500)]),
            log_date=today,
        )
        history = tracker.get_history(days=7)
        assert len(history) >= 1
