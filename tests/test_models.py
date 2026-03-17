"""Tests for Pydantic models."""

from datetime import date, datetime

import pytest

from nutrisnap.models import DailyLog, Food, Meal, MealType, NutritionInfo


class TestNutritionInfo:
    def test_zero(self):
        z = NutritionInfo.zero()
        assert z.calories == 0
        assert z.protein == 0
        assert z.carbs == 0
        assert z.fat == 0
        assert z.fiber == 0

    def test_scale(self):
        info = NutritionInfo(calories=200, protein=10, carbs=30, fat=8, fiber=5)
        scaled = info.scale(0.5)
        assert scaled.calories == 100.0
        assert scaled.protein == 5.0
        assert scaled.carbs == 15.0
        assert scaled.fat == 4.0
        assert scaled.fiber == 2.5

    def test_add(self):
        a = NutritionInfo(calories=100, protein=5, carbs=20, fat=3, fiber=2)
        b = NutritionInfo(calories=200, protein=10, carbs=30, fat=8, fiber=5)
        total = a + b
        assert total.calories == 300
        assert total.protein == 15
        assert total.carbs == 50
        assert total.fat == 11
        assert total.fiber == 7

    def test_scale_includes_vitamins(self):
        info = NutritionInfo(
            calories=100, protein=5, carbs=10, fat=3, fiber=2,
            vitamin_a=100, vitamin_c=50, calcium=200, iron=5,
        )
        scaled = info.scale(2.0)
        assert scaled.vitamin_a == 200.0
        assert scaled.vitamin_c == 100.0
        assert scaled.calcium == 400.0
        assert scaled.iron == 10.0


class TestFood:
    def test_food_creation(self):
        nutrition = NutritionInfo(calories=52, protein=0.3, carbs=13.8, fat=0.2, fiber=2.4)
        food = Food(
            name="apple",
            confidence=0.95,
            portion_grams=182,
            nutrition_per_100g=nutrition,
            nutrition_actual=nutrition.scale(1.82),
        )
        assert food.name == "apple"
        assert food.confidence == 0.95
        assert food.portion_grams == 182
        assert food.nutrition_actual.calories == pytest.approx(94.6, abs=0.1)


class TestMeal:
    def test_total_nutrition(self):
        n1 = NutritionInfo(calories=100, protein=5, carbs=20, fat=3, fiber=2)
        n2 = NutritionInfo(calories=200, protein=10, carbs=30, fat=8, fiber=5)
        foods = [
            Food(name="a", confidence=0.9, portion_grams=100,
                 nutrition_per_100g=n1, nutrition_actual=n1),
            Food(name="b", confidence=0.8, portion_grams=100,
                 nutrition_per_100g=n2, nutrition_actual=n2),
        ]
        meal = Meal(meal_type=MealType.LUNCH, foods=foods)
        assert meal.total_calories == 300
        assert meal.total_nutrition.protein == 15

    def test_empty_meal(self):
        meal = Meal(meal_type=MealType.SNACK)
        assert meal.total_calories == 0


class TestDailyLog:
    def test_add_meal_and_total(self):
        log = DailyLog(log_date=date(2026, 1, 15))
        n = NutritionInfo(calories=500, protein=25, carbs=60, fat=15, fiber=8)
        food = Food(name="lunch", confidence=1.0, portion_grams=300,
                    nutrition_per_100g=n, nutrition_actual=n)
        meal = Meal(meal_type=MealType.LUNCH, foods=[food])
        log.add_meal(meal)
        assert log.meal_count == 1
        assert log.total_calories == 500

    def test_multiple_meals(self):
        log = DailyLog()
        for _ in range(3):
            n = NutritionInfo(calories=400, protein=20, carbs=50, fat=10, fiber=5)
            food = Food(name="item", confidence=1.0, portion_grams=100,
                        nutrition_per_100g=n, nutrition_actual=n)
            log.add_meal(Meal(meal_type=MealType.SNACK, foods=[food]))
        assert log.meal_count == 3
        assert log.total_calories == 1200
